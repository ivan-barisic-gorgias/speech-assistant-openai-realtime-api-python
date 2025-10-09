from collections import defaultdict
import os
import json
import base64
import asyncio
import websockets
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.websockets import WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse, Connect, Say, Stream
from dotenv import load_dotenv
from agent_config import SYSTEM_MESSAGE, TOOLS
from function_handlers import handle_function_call

load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PORT = int(os.getenv('PORT', 5050))
TEMPERATURE = float(os.getenv('TEMPERATURE', 0.7))
VOICE = 'cedar'
LOG_EVENT_TYPES = [
    'error', 'response.content.done', 'rate_limits.updated',
    'response.done', 'input_audio_buffer.committed',
    'input_audio_buffer.speech_stopped', 'input_audio_buffer.speech_started',
    'session.created', 'session.updated'
]
SHOW_TIMING_MATH = False

app = FastAPI()

if not OPENAI_API_KEY:
    raise ValueError('Missing the OpenAI API key. Please set it in the .env file.')

@app.get("/", response_class=JSONResponse)
async def index_page():
    return {"message": "Twilio Media Stream Server is running!"}

@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """Handle incoming call and return TwiML response to connect to Media Stream."""
    response = VoiceResponse()
    # response.say(
    #     "You are connected to the A. I. voice assistant, powered by Twilio and the Open A I Realtime API",
    #     voice="Google.en-US-Chirp3-HD-Aoede"
    # )
    host = request.url.hostname
    connect = Connect()
    connect.stream(url=f'wss://{host}/media-stream')
    response.append(connect)
    return HTMLResponse(content=str(response), media_type="application/xml")

@app.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connections between Twilio and OpenAI."""
    print("Client connected")
    await websocket.accept()

    async with websockets.connect(
        f"wss://api.openai.com/v1/realtime?model=gpt-realtime&temperature={TEMPERATURE}",
        additional_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
    ) as openai_ws:
        await initialize_session(openai_ws)

        # Connection specific state
        stream_sid = None
        latest_media_timestamp = 0
        last_assistant_item = None
        mark_queue = []
        response_start_timestamp_twilio = None
        
        # Audio buffering state for outgoing audio to Twilio
        outgoing_audio_buffer = bytearray()
        BUFFER_SIZE = 160  # 160 bytes per frame
        
        # Timing measurement for response latency
        user_speech_stopped_time = None
        agent_response_started_time = None
        
        async def receive_from_twilio():
            """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
            nonlocal stream_sid, latest_media_timestamp
            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    if data['event'] == 'media' and openai_ws.state.name == 'OPEN':
                        latest_media_timestamp = int(data['media']['timestamp'])
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": data['media']['payload']
                        }
                        await openai_ws.send(json.dumps(audio_append))
                    elif data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        print(f"Incoming stream has started {stream_sid}")
                        response_start_timestamp_twilio = None
                        latest_media_timestamp = 0
                        last_assistant_item = None
                        # Reset timing variables for new stream
                        user_speech_stopped_time = None
                        agent_response_started_time = None
                    elif data['event'] == 'mark':
                        if mark_queue:
                            mark_queue.pop(0)
            except WebSocketDisconnect:
                print("Client disconnected.")
                if openai_ws.state.name == 'OPEN':
                    await openai_ws.close()

        async def send_to_twilio():
            """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
            nonlocal stream_sid, last_assistant_item, response_start_timestamp_twilio, outgoing_audio_buffer, user_speech_stopped_time, agent_response_started_time
            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)
                    if response['type'] in LOG_EVENT_TYPES:
                        print(f"Received event: {response['type']}", response)
                        
                        # Track when user stops speaking
                        if response['type'] == 'input_audio_buffer.speech_stopped':
                            user_speech_stopped_time = asyncio.get_event_loop().time()
                            print(f"[TIMING] User speech stopped at: {user_speech_stopped_time:.3f}s")

                    if response.get('type') == 'response.output_audio.delta' and 'delta' in response:
                        # Track when agent starts responding (first audio delta)
                        if agent_response_started_time is None:
                            agent_response_started_time = asyncio.get_event_loop().time()
                            print(f"[TIMING] Agent response started at: {agent_response_started_time:.3f}s")
                            
                            # Calculate and log response latency
                            if user_speech_stopped_time is not None:
                                response_latency = agent_response_started_time - user_speech_stopped_time
                                print(f"[TIMING] Response latency: {response_latency:.3f}s ({response_latency*1000:.0f}ms)")
                            else:
                                print(f"[TIMING] No user speech stop time recorded, cannot calculate latency")
                        
                        # Decode the base64 audio delta from OpenAI
                        audio_data = base64.b64decode(response['delta'])
                        
                        # Add to outgoing buffer
                        outgoing_audio_buffer.extend(audio_data)
                        
                        # Send complete 160-byte frames to Twilio
                        while len(outgoing_audio_buffer) >= BUFFER_SIZE:
                            # Extract 160 bytes from buffer
                            frame_data = outgoing_audio_buffer[:BUFFER_SIZE]
                            outgoing_audio_buffer = outgoing_audio_buffer[BUFFER_SIZE:]
                            
                            # Encode frame back to base64
                            frame_payload = base64.b64encode(frame_data).decode('utf-8')
                            
                            # Send to Twilio
                            audio_delta = {
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {
                                    "payload": frame_payload
                                }
                            }
                            await websocket.send_json(audio_delta)


                        if response.get("item_id") and response["item_id"] != last_assistant_item:
                            response_start_timestamp_twilio = latest_media_timestamp
                            last_assistant_item = response["item_id"]
                            # Reset timing variables for new response
                            agent_response_started_time = None
                            if SHOW_TIMING_MATH:
                                print(f"Setting start timestamp for new response: {response_start_timestamp_twilio}ms")

                        await send_mark(websocket, stream_sid)

                    # Trigger an interruption. Your use case might work better using `input_audio_buffer.speech_stopped`, or combining the two.
                    if response.get('type') == 'input_audio_buffer.speech_started':
                        print("Speech started detected.")
                        if last_assistant_item:
                            print(f"Interrupting response with id: {last_assistant_item}")
                            await handle_speech_started_event()
                    
                    # ---- TOOL CALL HANDLING ----
                    # a) arguments streaming
                    if response.get("type") == "response.function_call_arguments.delta":
                        call_id = response["call_id"]
                        arg_buffers[call_id].append(response.get("delta", ""))
                        continue

                    # b) arguments done -> we have full payload and the tool name
                    if response.get("type") == "response.function_call_arguments.done":
                        call_id = response["call_id"]
                        tool_name = response["name"]
                        full_args = "".join(arg_buffers.pop(call_id, []))  # JSON string

                        try:
                            args = json.loads(full_args) if full_args else {}
                        except json.JSONDecodeError:
                            args = {"_raw": full_args}

                        # run your handler (HTTP/RAG/etc.)
                        result = await route_tool_call(tool_name, args)

                        # Store the function call result, but don't send yet - wait for response.done
                        completed_function_calls.append({
                            "call_id": call_id,
                            "result": result
                        })
                        continue

                    # Handle response.done - flush audio buffer and process function calls if any
                    if response.get("type") == "response.done":
                        # Flush any remaining audio buffer when response is done
                        await flush_audio_buffer()
                        
                        if completed_function_calls:
                            print(f"[OPENAI REALTIME] Processing {len(completed_function_calls)} function call results after response.done")

                            # Send all function call outputs
                            for func_call in completed_function_calls:
                                function_output_item = {
                                    "type": "conversation.item.create",
                                    "item": {
                                        "type": "function_call_output",
                                        "call_id": func_call["call_id"],
                                        "output": json.dumps(func_call["result"])
                                    }
                                }
                                print(f"[OPENAI REALTIME] Sending function call output for call_id: {func_call['call_id']}")
                                await openai_ws.send(json.dumps(function_output_item))

                            # Clear the buffer
                            completed_function_calls.clear()

                            # Create a response to continue the conversation
                            response_create = {
                                "type": "response.create"
                            }
                            print(f"[OPENAI REALTIME] Sending response.create to continue conversation")
                            await openai_ws.send(json.dumps(response_create))
                        continue
                    # ---- END TOOL CALL HANDLING ----

            except Exception as e:
                print(f"Error in send_to_twilio: {e}")

        async def handle_speech_started_event():
            """Handle interruption when the caller's speech starts."""
            nonlocal response_start_timestamp_twilio, last_assistant_item, outgoing_audio_buffer, user_speech_stopped_time, agent_response_started_time
            print("Handling speech started event.")
            
            # Reset timing variables on interruption
            user_speech_stopped_time = None
            agent_response_started_time = None
            
            # Flush any remaining audio buffer before interruption
            await flush_audio_buffer()
            
            if mark_queue and response_start_timestamp_twilio is not None:
                elapsed_time = latest_media_timestamp - response_start_timestamp_twilio
                if SHOW_TIMING_MATH:
                    print(f"Calculating elapsed time for truncation: {latest_media_timestamp} - {response_start_timestamp_twilio} = {elapsed_time}ms")

                if last_assistant_item:
                    if SHOW_TIMING_MATH:
                        print(f"Truncating item with ID: {last_assistant_item}, Truncated at: {elapsed_time}ms")

                    truncate_event = {
                        "type": "conversation.item.truncate",
                        "item_id": last_assistant_item,
                        "content_index": 0,
                        "audio_end_ms": elapsed_time
                    }
                    await openai_ws.send(json.dumps(truncate_event))

                await websocket.send_json({
                    "event": "clear",
                    "streamSid": stream_sid
                })

                mark_queue.clear()
                last_assistant_item = None
                response_start_timestamp_twilio = None
                # Clear the audio buffer on interruption
                outgoing_audio_buffer = bytearray()

        async def flush_audio_buffer():
            """Flush any remaining audio buffer to Twilio."""
            nonlocal outgoing_audio_buffer
            if outgoing_audio_buffer and stream_sid:
                # Send remaining audio data as-is (no padding to avoid audio pops)
                frame_payload = base64.b64encode(outgoing_audio_buffer).decode('utf-8')
                audio_delta = {
                    "event": "media",
                    "streamSid": stream_sid,
                    "media": {
                        "payload": frame_payload
                    }
                }
                await websocket.send_json(audio_delta)
                outgoing_audio_buffer = bytearray()

        async def send_mark(connection, stream_sid):
            if stream_sid:
                mark_event = {
                    "event": "mark",
                    "streamSid": stream_sid,
                    "mark": {"name": "responsePart"}
                }
                await connection.send_json(mark_event)
                mark_queue.append('responsePart')

        await asyncio.gather(receive_from_twilio(), send_to_twilio())

async def send_initial_conversation_item(openai_ws):
    """Send initial conversation item if AI talks first."""
    initial_conversation_item = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "Greet the user with 'Hello! Welcome to our voice assistant. How can I help you today?'"
                }
            ]
        }
    }
    await openai_ws.send(json.dumps(initial_conversation_item))
    await openai_ws.send(json.dumps({"type": "response.create"}))


async def initialize_session(openai_ws):
    """Control initial session with OpenAI."""
    session_update = {
        "type": "session.update",
        "session": {
            "type": "realtime",
            "model": "gpt-realtime",
            "output_modalities": ["audio"],
            "audio": {
                "input": {
                    "format": {"type": "audio/pcmu"},
                    # "turn_detection": { 
                    #     "type": "semantic_vad", 
                    #     "create_response": True,
                    #     "eagerness": "auto"
                    # }
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 200,
                        "silence_duration_ms": 200,
                        "create_response": True,
                        "interrupt_response": True
                    }
                },
                "output": {
                    "format": {"type": "audio/pcmu"},
                    "voice": VOICE
                }
            },
            "instructions": SYSTEM_MESSAGE,
            "tools": TOOLS,
        }
    }
    print('Sending session update:', json.dumps(session_update))
    await openai_ws.send(json.dumps(session_update))

    # Uncomment the next line to have the AI speak first
    await send_initial_conversation_item(openai_ws)


arg_buffers = defaultdict(list)
completed_function_calls = []  # Buffer for function calls waiting for response.done

async def route_tool_call(name: str, args: dict):
    """Route tool calls to our function handlers."""
    print(f"[OPENAI REALTIME] Tool call received: {name}")
    print(f"[OPENAI REALTIME] Tool arguments: {args}")

    result, error = handle_function_call(name, args)

    if result is not None:
        print(f"[OPENAI REALTIME] Tool call successful: {result}")
        return result
    else:
        print(f"[OPENAI REALTIME] Tool call failed: {error}")
        return {"error": error}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
