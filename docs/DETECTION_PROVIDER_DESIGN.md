# Detection Provider Module - System Design & Data-Flow Specification

**Version:** 1.0
**Date:** November 6, 2025
**Status:** Design Specification
**Classification:** Implementation-Agnostic Architecture

---

## 📋 Document Overview

This document provides a comprehensive system design and data-flow plan for the **Detection Provider** module of an industry-grade CCTV monitoring and face-recognition attendance system. It defines the complete request/response data structures, processing flows, integration patterns, and scalability strategies—ready for implementation by any development team.

**Document Purpose:**
- Define Detection Provider architecture and responsibilities
- Specify request/response schemas and data flows
- Document multi-stream handling and concurrency patterns
- Establish model management and fallback strategies
- Plan logging, audit trails, and regulatory compliance
- Design GUI/API integration patterns
- Provide scalability and future extension roadmap

**Audience:** System Architects, Backend Engineers, DevOps Engineers, Technical Product Managers

---

## 📚 Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Module Overview](#2-module-overview)
   - [2.1 Purpose](#21-purpose)
   - [2.2 Core Responsibilities](#22-core-responsibilities)
   - [2.3 System Integration](#23-system-integration)
3. [Supported Stream Types](#3-supported-stream-types)
   - [3.1 Stream Type Specifications](#31-stream-type-specifications)
   - [3.2 Stream Identification](#32-stream-identification)
   - [3.3 Concurrent Stream Handling](#33-concurrent-stream-handling)
   - [3.4 Frame Buffering & Synchronization](#34-frame-buffering--synchronization)
4. [Request Flow - Frame-to-Detection Pipeline](#4-request-flow---frame-to-detection-pipeline)
   - [4.1 Input Structure](#41-input-structure)
   - [4.2 Processing Pipeline](#42-processing-pipeline)
   - [4.3 Queuing & Batching Strategy](#43-queuing--batching-strategy)
5. [Response Flow - Detection Results](#5-response-flow---detection-results)
   - [5.1 Output Structure](#51-output-structure)
   - [5.2 Error & Edge Cases](#52-error--edge-cases)
   - [5.3 Asynchronous Response](#53-asynchronous-response)
6. [Multi-Stream & Concurrency](#6-multi-stream--concurrency)
   - [6.1 Architecture](#61-architecture)
   - [6.2 Concurrency Strategies](#62-concurrency-strategies)
   - [6.3 Session Management](#63-session-management)
   - [6.4 Resource Allocation](#64-resource-allocation)
7. [Model Management & Fallback](#7-model-management--fallback)
   - [7.1 Model Selection](#71-model-selection)
   - [7.2 GPU vs CPU Mode](#72-gpu-vs-cpu-mode)
   - [7.3 Fallback Chain](#73-fallback-chain)
   - [7.4 Performance Optimization](#74-performance-optimization)
8. [Logging & Audit Trail](#8-logging--audit-trail)
   - [8.1 Event Types](#81-event-types)
   - [8.2 Storage Strategy](#82-storage-strategy)
   - [8.3 Log Entry Structure](#83-log-entry-structure)
   - [8.4 Audit Trail Requirements](#84-audit-trail-requirements)
9. [Integration with GUI/API](#9-integration-with-guiapi)
   - [9.1 Communication Protocols](#91-communication-protocols)
   - [9.2 Update Frequency](#92-update-frequency)
   - [9.3 Client Integration Examples](#93-client-integration-examples)
10. [Future Scalability Plan](#10-future-scalability-plan)
    - [10.1 Horizontal Scaling](#101-horizontal-scaling)
    - [10.2 Microservice Decomposition](#102-microservice-decomposition)
    - [10.3 Multi-Site Deployment](#103-multi-site-deployment)
    - [10.4 Extension to Other Detection Tasks](#104-extension-to-other-detection-tasks)
11. [Implementation Roadmap](#11-implementation-roadmap)

---

## 1. Executive Summary

The **Detection Provider** is a critical service layer in an industry-grade CCTV monitoring and face-recognition attendance system. It acts as the central orchestrator that:

- ✅ Receives frames/streams from multiple heterogeneous camera sources (RTSP, USB, HTTP, WebSocket, Socket)
- ✅ Performs face detection, recognition, and person identification
- ✅ Manages concurrent processing of multiple streams
- ✅ Implements intelligent model selection with GPU/CPU fallback
- ✅ Returns structured, real-time results to GUI/API clients
- ✅ Ensures high availability, scalability, and fault tolerance

### Key Design Principles

1. **Abstraction**: Hide complexity of multiple camera types and ML models from clients
2. **Scalability**: Handle 1-100+ concurrent camera streams efficiently
3. **Reliability**: Ensure continuous operation with automatic failover and retry mechanisms
4. **Real-time Performance**: Process frames with <200ms latency for interactive applications
5. **Extensibility**: Support future detection types (vehicles, objects, activities)

### Architecture at a Glance

```mermaid
graph TB
    subgraph "Camera Sources"
        C1[RTSP Cameras]
        C2[USB Cameras]
        C3[HTTP MJPEG]
        C4[WebSocket]
        C5[Socket Streams]
    end

    subgraph "Detection Provider Core"
        SM[Stream Manager]
        PE[Processing Engine]
        RE[Recognition Engine]
        RM[Result Manager]
    end

    subgraph "Clients"
        GUI[GUI Frontend]
        API[REST API]
        WS[WebSocket Hub]
    end

    subgraph "Infrastructure"
        DB[(PostgreSQL)]
        REDIS[(Redis)]
        STORAGE[(MinIO)]
        MQ[Message Queue]
    end

    C1 --> SM
    C2 --> SM
    C3 --> SM
    C4 --> SM
    C5 --> SM

    SM --> PE
    PE --> RE
    RE --> RM

    RM --> GUI
    RM --> API
    RM --> WS

    RM --> DB
    RM --> REDIS
    RM --> STORAGE
    PE --> MQ
```

---

## 2. Module Overview

### 2.1 Purpose

The Detection Provider serves as the **intelligent middleware** between raw camera feeds and the application's business logic. Its core mission is to transform unstructured video frames into structured, actionable detection events.

**Key Objectives:**
- **Abstraction**: Hide complexity of multiple camera types and ML models from clients
- **Orchestration**: Coordinate frame capture, queuing, detection, recognition, and result delivery
- **Scalability**: Handle 1-100+ concurrent camera streams efficiently
- **Reliability**: Ensure continuous operation with automatic failover and retry mechanisms
- **Real-time Performance**: Process frames with <200ms latency for interactive applications

### 2.2 Core Responsibilities

#### 2.2.1 Frame Capture & Stream Management
- Maintain persistent connections to heterogeneous camera sources
- Extract frames at configurable intervals (1-30 FPS)
- Buffer frames with backpressure handling
- Synchronize timestamps across distributed cameras
- Monitor stream health and trigger reconnection on failure

#### 2.2.2 Detection & Recognition Orchestration
- Queue frames for processing with priority-based scheduling
- Invoke face detection models to locate faces in frames
- Extract face embeddings (128-d/512-d vectors) for recognition
- Compare embeddings against enrolled person database
- Apply confidence thresholds and matching policies

#### 2.2.3 Result Packaging & Delivery
- Structure detection results in standardized JSON format
- Generate bounding boxes, confidence scores, person identities
- Create face snapshots and upload to object storage
- Cache results in Redis for low-latency access
- Broadcast real-time updates via WebSocket

#### 2.2.4 Model Management & Fallback
- Support multiple detection/recognition models (GPU-optimized, CPU-friendly, lightweight)
- Implement intelligent fallback chain: GPU → CPU → Cloud API
- Monitor model performance metrics (latency, throughput, accuracy)
- Enable runtime model switching without service interruption

#### 2.2.5 Error Handling & Resilience
- Gracefully handle camera disconnections, network failures, model crashes
- Implement exponential backoff for reconnection attempts
- Queue failed frames for retry
- Maintain detailed audit logs for troubleshooting

### 2.3 System Integration

```mermaid
graph TB
    subgraph "System Architecture"
        subgraph "Cameras"
            RTSP[RTSP Cameras]
            USB[USB Cameras]
            HTTP[HTTP MJPEG]
            WEBSOCKET[WebSocket]
            SOCKET[Socket Streams]
        end

        subgraph "Detection Provider Core"
            SM[Stream Manager<br/>- Connection Pool<br/>- Frame Extractor<br/>- Health Monitor]
            PE[Processing Engine<br/>- Detection Queue<br/>- Model Orchestrator<br/>- Batch Processor]
            RE[Recognition Engine<br/>- Face Encoder<br/>- Embedding Matcher<br/>- Person Linker]
            RM[Result Manager<br/>- Storage Handler<br/>- Cache Manager<br/>- Event Broadcaster]
        end

        subgraph "Client Layer"
            GUI[GUI Frontend<br/>- Live View<br/>- Playback<br/>- Config]
            RESTAPI[REST API<br/>Gateway]
            WSHUB[WebSocket Hub<br/>- Real-time Updates<br/>- Subscriptions]
        end

        subgraph "Supporting Services"
            POSTGRES[(PostgreSQL<br/>- Metadata<br/>- History<br/>- Persons)]
            REDIS[(Redis<br/>- Cache<br/>- Queues<br/>- Sessions)]
            MINIO[(MinIO<br/>- Snapshots<br/>- Videos<br/>- Faces)]
            CELERY[Celery<br/>- Workers<br/>- Scheduler<br/>- Beat]
            ML[ML Models<br/>- Detection<br/>- Recognition<br/>- Fallbacks]
            MONITOR[Monitoring<br/>- Metrics<br/>- Alerts<br/>- Logs]
        end

        RTSP --> SM
        USB --> SM
        HTTP --> SM
        WEBSOCKET --> SM
        SOCKET --> SM

        SM --> PE
        PE --> RE
        RE --> RM

        RM --> GUI
        RM --> RESTAPI
        RM --> WSHUB

        RM --> POSTGRES
        RM --> REDIS
        RM --> MINIO
        PE --> CELERY
        PE --> ML
        RM --> MONITOR
    end
```

**Integration Touchpoints:**

1. **GUI Frontend (React + WebSocket)**
   - Receives real-time detection events via WebSocket
   - Displays live bounding boxes and person identities
   - Configures camera settings and detection parameters
   - Queries historical detections via REST API

2. **API Gateway (FastAPI)**
   - Exposes RESTful endpoints for detection queries
   - Manages camera CRUD operations
   - Configures detection provider settings
   - Handles authentication and authorization

3. **Model Services (Internal/External)**
   - GPU-accelerated face detection (YOLO, RetinaFace, MTCNN)
   - Face encoding models (FaceNet, ArcFace, dlib)
   - External ML APIs (AWS Rekognition, Azure Face API) as fallback

4. **Database (PostgreSQL)**
   - Stores detection metadata (timestamps, bounding boxes, confidence)
   - Maintains person registry with face encodings
   - Tracks attendance records linked to detections

5. **Cache Layer (Redis)**
   - Caches live detections (3-second TTL)
   - Maintains WebSocket session state
   - Queues frames for asynchronous processing

6. **Object Storage (MinIO/S3)**
   - Stores face snapshots (JPEG/PNG)
   - Archives video clips for playback
   - Manages retention policies

7. **Task Queue (Celery)**
   - Asynchronous frame processing
   - Batch encoding generation
   - Periodic cleanup and health checks

---

## 3. Supported Stream Types

The Detection Provider must handle diverse camera sources with varying protocols, reliability characteristics, and performance profiles.

### 3.1 Stream Type Specifications

#### 3.1.1 RTSP (Real-Time Streaming Protocol)

**Characteristics:**
- Industry standard for IP cameras
- Supports H.264/H.265 video codecs
- Typically 1080p @ 15-30 FPS
- Requires authentication (username/password)

**Connection Parameters:**
```json
{
  "stream_type": "RTSP",
  "rtsp_url": "rtsp://192.168.1.100:554/stream1",
  "transport": "tcp",
  "username": "admin",
  "password": "encrypted_password",
  "codec": "h264",
  "resolution": "1920x1080",
  "fps": 25,
  "timeout_seconds": 10
}
```

**Handling Strategy:**
- Use FFmpeg for frame extraction
- Maintain persistent connection with keep-alive
- Reconnect on timeout with exponential backoff (1s, 2s, 4s, 8s, max 60s)
- Buffer last 10 frames for smooth processing

#### 3.1.2 USB/Local Camera

**Characteristics:**
- Direct connection to server (0-indexed device IDs)
- Lower resolution (720p typical)
- Zero network latency
- Limited to single server

**Connection Parameters:**
```json
{
  "stream_type": "USB",
  "device_id": 0,
  "resolution": "1280x720",
  "fps": 30,
  "backend": "v4l2"
}
```

**Handling Strategy:**
- Use OpenCV VideoCapture
- Auto-detect on startup (enumerate devices)
- Monitor for device disconnection
- No buffering (real-time only)

#### 3.1.3 HTTP MJPEG (Motion JPEG over HTTP)

**Characteristics:**
- Simple HTTP streaming of JPEG frames
- Higher bandwidth than H.264
- Easy to debug (standard HTTP)
- Common in older IP cameras

**Connection Parameters:**
```json
{
  "stream_type": "HTTP_MJPEG",
  "url": "http://192.168.1.101:8080/video",
  "auth_type": "basic",
  "username": "user",
  "password": "encrypted_password",
  "headers": {
    "User-Agent": "DetectionProvider/1.0"
  }
}
```

**Handling Strategy:**
- Use aiohttp for async HTTP streaming
- Parse multipart/x-mixed-replace boundary
- Extract JPEG frames from chunks
- Implement connection pooling

#### 3.1.4 WebSocket Stream

**Characteristics:**
- Bidirectional communication
- Browser-based cameras (WebRTC fallback)
- Server can control camera settings
- Lower latency than HTTP

**Connection Parameters:**
```json
{
  "stream_type": "WEBSOCKET",
  "ws_url": "ws://192.168.1.102:8080/stream",
  "protocol": "binary",
  "ping_interval": 30,
  "max_message_size": 5242880
}
```

**Handling Strategy:**
- Use websockets library (async)
- Send heartbeat pings every 30s
- Handle binary frames directly
- Decode base64 if protocol="base64"

#### 3.1.5 Raw Socket Stream (Custom Protocol)

**Characteristics:**
- Custom binary protocol
- Maximum performance (no HTTP overhead)
- Requires custom client implementation
- Used for proprietary camera systems

**Connection Parameters:**
```json
{
  "stream_type": "SOCKET",
  "host": "192.168.1.103",
  "port": 9000,
  "protocol": "custom_v1",
  "frame_delimiter": "\\xFF\\xD8\\xFF\\xE0",
  "keepalive": true
}
```

**Handling Strategy:**
- Use asyncio streams (StreamReader/StreamWriter)
- Implement protocol parser
- Handle frame framing/delimiter detection
- Enable TCP keepalive

### 3.2 Stream Identification

Each camera stream is uniquely identified by a **camera_id** (UUID) assigned at registration.

**Camera Registry Schema:**
```json
{
  "camera_id": "cam_550e8400-e29b-41d4-a716-446655440000",
  "name": "Main Entrance",
  "location": {
    "site": "HQ Building",
    "floor": 1,
    "zone": "Lobby",
    "coordinates": {
      "latitude": 37.7749,
      "longitude": -122.4194
    }
  },
  "stream_config": {
    "stream_type": "RTSP",
    "rtsp_url": "rtsp://192.168.1.100:554/stream1"
  },
  "detection_config": {
    "enabled": true,
    "fps_limit": 5,
    "min_face_size": 80,
    "confidence_threshold": 0.65,
    "max_faces_per_frame": 10
  },
  "status": {
    "state": "live",
    "last_connected": "2025-11-06T10:30:00Z",
    "uptime_seconds": 86400,
    "frames_processed": 432000,
    "error_count": 3,
    "last_error": "Connection timeout after 10s"
  }
}
```

**Stream Session Tracking:**
```json
{
  "session_id": "sess_7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "camera_id": "cam_550e8400-e29b-41d4-a716-446655440000",
  "started_at": "2025-11-06T10:30:00Z",
  "last_frame_at": "2025-11-06T12:45:23Z",
  "frames_captured": 54000,
  "frames_processed": 10800,
  "frames_dropped": 120,
  "avg_latency_ms": 145,
  "connection_resets": 2
}
```

### 3.3 Concurrent Stream Handling

**Concurrency Model:**
- One **dedicated async task** per camera stream
- Frame extraction runs in background coroutine
- Detection processing uses **thread pool** (for CPU-bound ML models) or **async queue** (for GPU models)
- Results delivered via **shared message bus** (Redis pub/sub)

```mermaid
graph LR
    subgraph "Detection Provider Process"
        C1[Camera 1] --> AT1[Async Task 1]
        C2[Camera 2] --> AT2[Async Task 2]
        C3[Camera 3] --> AT3[Async Task 3]
        CN[Camera N] --> ATN[Async Task N]

        AT1 --> FQ[Frame Queue]
        AT2 --> FQ
        AT3 --> FQ
        ATN --> FQ

        FQ --> TP[Thread Pool<br/>Detection Workers]
        TP --> RQ[Result Queue]
        RQ --> BT[Broadcaster Task]
        BT --> WS[WebSocket Clients]
    end
```

**Resource Allocation:**
- **Vertical**: Up to 20 cameras per instance (4-core, 16GB RAM, GPU)
- **Horizontal**: Multiple Detection Provider instances behind load balancer
- **Camera Assignment**: Sticky routing by camera_id hash

**Scaling Strategy:**
```mermaid
graph TB
    LB[Load Balancer]
    LB --> DP1[Detection Provider 1<br/>Cameras 1-20<br/>GPU-0]
    LB --> DP2[Detection Provider 2<br/>Cameras 21-40<br/>GPU-1]
    LB --> DPN[Detection Provider N<br/>Cameras 81-100<br/>CPU]

    DP1 --> REDIS[(Redis<br/>Shared Queue)]
    DP2 --> REDIS
    DPN --> REDIS
```

### 3.4 Frame Buffering & Synchronization

**Frame Buffer Design:**
- Circular buffer per camera (size: 10 frames)
- Overflow strategy: drop oldest frame
- Metadata: timestamp, sequence number, camera_id

**Timestamp Synchronization:**
- Use **server timestamp** as source of truth (cameras may have clock drift)
- Record both `frame_timestamp` (camera time) and `received_timestamp` (server time)
- Calculate latency: `received_timestamp - frame_timestamp`

**Frame Schema:**
```json
{
  "frame_id": "frame_12345678",
  "camera_id": "cam_550e8400-e29b-41d4-a716-446655440000",
  "sequence_number": 12345678,
  "camera_timestamp": "2025-11-06T12:45:23.123Z",
  "received_timestamp": "2025-11-06T12:45:23.268Z",
  "latency_ms": 145,
  "frame_data": "<binary JPEG or base64>",
  "format": "jpeg",
  "resolution": {
    "width": 1920,
    "height": 1080
  },
  "size_bytes": 245678
}
```

---

## 4. Request Flow - Frame-to-Detection Pipeline

### 4.1 Input Structure

Detection can be triggered via two modes:
1. **Push Mode**: Client sends individual frames via API
2. **Stream Mode**: Detection Provider pulls frames from active streams

#### 4.1.1 Push Mode Request Schema

**Endpoint:** `POST /api/v1/detections/process-frame`

**Request Body:**
```json
{
  "camera_id": "cam_550e8400-e29b-41d4-a716-446655440000",
  "stream_type": "RTSP",
  "frame_id": "frame_12345678",
  "timestamp": "2025-11-06T12:45:23.123Z",
  "frame_data": "base64_encoded_jpeg_or_png",
  "frame_metadata": {
    "format": "jpeg",
    "resolution": {
      "width": 1920,
      "height": 1080
    },
    "size_bytes": 245678,
    "codec": "h264"
  },
  "detection_options": {
    "model_type": "face-recognition",
    "models": {
      "detection": "retinaface-gpu",
      "recognition": "arcface-512d"
    },
    "parameters": {
      "min_confidence": 0.65,
      "min_face_size": 80,
      "max_faces": 10,
      "return_snapshots": true,
      "return_embeddings": false
    },
    "processing": {
      "priority": "normal",
      "timeout_ms": 5000,
      "async": false
    }
  },
  "client_context": {
    "client_id": "gui-frontend-12345",
    "request_id": "req_abc123",
    "callback_url": "https://app.example.com/detection-callback"
  }
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `camera_id` | UUID | Yes | Unique camera identifier |
| `stream_type` | Enum | Yes | One of: RTSP, USB, HTTP_MJPEG, WEBSOCKET, SOCKET |
| `frame_id` | String | Yes | Unique frame identifier (for deduplication) |
| `timestamp` | ISO 8601 | Yes | Frame capture timestamp |
| `frame_data` | Base64 | Yes | Image data (JPEG/PNG encoded) |
| `model_type` | Enum | No | face-recognition, face-detection, person-detection |
| `min_confidence` | Float | No | Threshold for accepting detections (0.0-1.0) |
| `max_faces` | Int | No | Maximum faces to process in frame |
| `return_snapshots` | Bool | No | Generate cropped face images |
| `priority` | Enum | No | Processing priority (affects queue position) |
| `async` | Bool | No | Queue for background processing vs synchronous |

#### 4.1.2 Stream Mode: Automatic Frame Extraction

When a camera is registered with `detection_enabled: true`, the Detection Provider automatically:
1. Establishes connection to stream
2. Extracts frames at configured FPS (e.g., 5 FPS from 25 FPS stream)
3. Queues frames for processing
4. Broadcasts results to subscribed clients

**No explicit API call needed** - fully autonomous operation.

### 4.2 Processing Pipeline

```mermaid
flowchart TD
    Start[Frame Received] --> Validate[Validate & Parse<br/>- Check format<br/>- Decode base64<br/>- Validate camera_id]
    Validate --> Dedup{Deduplication<br/>Check Redis}
    Dedup -->|Duplicate| Skip[Return: Already Processed]
    Dedup -->|New| Priority[Priority Assignment<br/>- Urgent: Skip queue<br/>- High: Priority queue<br/>- Normal: Standard<br/>- Low: Background]

    Priority --> Enqueue[Enqueue to<br/>Detection Queue<br/>Redis/Celery/In-memory]
    Enqueue --> Acquire[Acquire Resources<br/>- GPU slot<br/>- CPU thread<br/>- Rate limiting]

    Acquire --> Detect[Face Detection<br/>YOLO/RetinaFace/MTCNN<br/>Output: Bounding boxes]
    Detect --> Filter[Quality Filtering<br/>- Blur detection<br/>- Size filtering<br/>- Confidence threshold]

    Filter --> Encode[Face Encoding<br/>Crop + Resize<br/>Generate 128-d/512-d embedding]
    Encode --> Lookup[Database Lookup<br/>Calculate similarity<br/>Find best match]

    Lookup --> Link[Person Linking<br/>Match: link person_id<br/>No match: Unknown]
    Link --> Snapshot[Generate Snapshots<br/>Crop face<br/>Upload to MinIO]

    Snapshot --> Structure[Structure Response<br/>Package JSON<br/>Calculate metrics]
    Structure --> Persist[Persist to PostgreSQL<br/>Index for queries]

    Persist --> Cache[Cache in Redis<br/>3s TTL for live view<br/>Update statistics]
    Cache --> Broadcast[Broadcast to Clients<br/>WebSocket pub/sub<br/>Invoke callbacks]
    Broadcast --> End[Detection Complete]
```

**Processing Steps Explained:**

1. **Frame Ingestion**
   - Receive frame from API or stream
   - Validate format and parse metadata
   - Check camera_id exists in registry

2. **Deduplication**
   - Check frame_id in Redis (5-second TTL)
   - Skip if already processed

3. **Queuing Strategy**
   - Assign priority (urgent/high/normal/low)
   - Enqueue to Redis Sorted Set or Celery task queue

4. **Model Invocation**
   - Acquire GPU/CPU resources
   - Run face detection model
   - Output: Bounding boxes + confidence scores

5. **Quality Filtering**
   - Filter blurry faces (Laplacian variance)
   - Filter small faces (< min_size pixels)
   - Filter low confidence (< threshold)

6. **Face Encoding**
   - Crop face region from frame
   - Resize to model input size (160x160 or 112x112)
   - Generate embedding vector

7. **Recognition**
   - Load enrolled person embeddings from database
   - Calculate cosine similarity or Euclidean distance
   - Find best match above threshold

8. **Result Generation**
   - Generate face snapshots
   - Upload to object storage
   - Structure response JSON

9. **Delivery**
   - Persist to PostgreSQL
   - Cache in Redis (3s TTL)
   - Broadcast to WebSocket subscribers

### 4.3 Queuing & Batching Strategy

#### 4.3.1 Multiple Arrival Scenarios

| Scenario | Traffic | Strategy | Latency |
|----------|---------|----------|---------|
| **Low Traffic** | < 10 frames/sec | Synchronous processing | 100-200ms |
| **Moderate Traffic** | 10-50 frames/sec | Queue + batch (4-8 frames) | 200-500ms |
| **High Traffic** | > 50 frames/sec | Distributed workers + priority queue | 500-2000ms |

#### 4.3.2 Queue Management

**Queue Data Structure (Redis Sorted Set):**
```
Key: detection:queue:{priority}
Score: timestamp_ms (FIFO within priority)
Value: JSON serialized frame metadata + pointer to frame blob

Example:
ZADD detection:queue:high 1699274723123 '{"frame_id": "frame_123", "camera_id": "cam_001", "blob_key": "frames:frame_123"}'
```

**Queue Processing Loop:**
```
WHILE true:
  1. Check GPU/CPU capacity (max_concurrent_jobs)
  2. If capacity available:
     a. ZPOPMIN detection:queue:urgent 1
     b. If empty: ZPOPMIN detection:queue:high 1
     c. If empty: ZPOPMIN detection:queue:normal 1
     d. If empty: ZPOPMIN detection:queue:low 1
  3. If frame found:
     a. Fetch frame blob from Redis/MinIO
     b. Submit to model worker
  4. SLEEP 10ms
```

#### 4.3.3 Deduplication

```
Before queuing:
  frame_key = f"detection:processed:{frame_id}"
  exists = REDIS.EXISTS(frame_key)
  if exists:
    RETURN {"status": "duplicate", "message": "Frame already processed"}
  else:
    REDIS.SETEX(frame_key, 5, "1")  # 5-second TTL
    PROCEED to queue
```

---

## 5. Response Flow - Detection Results

### 5.1 Output Structure

**Endpoint:** `POST /api/v1/detections/process-frame` (synchronous response)

**Response Schema:**
```json
{
  "status": "success",
  "message": "Frame processed successfully",
  "processing_info": {
    "frame_id": "frame_12345678",
    "camera_id": "cam_550e8400-e29b-41d4-a716-446655440000",
    "camera_name": "Main Entrance",
    "timestamp": "2025-11-06T12:45:23.123Z",
    "processing_started_at": "2025-11-06T12:45:23.268Z",
    "processing_completed_at": "2025-11-06T12:45:23.395Z",
    "processing_time_ms": 127,
    "queue_time_ms": 34,
    "detection_time_ms": 78,
    "recognition_time_ms": 15
  },
  "detections": [
    {
      "detection_id": "det_abc12345",
      "detection_type": "face",
      "bounding_box": {
        "x": 120,
        "y": 85,
        "width": 120,
        "height": 135,
        "normalized": {
          "x": 0.0625,
          "y": 0.0787,
          "width": 0.0625,
          "height": 0.125
        }
      },
      "confidence": 0.93,
      "person": {
        "person_id": "per_201",
        "employee_id": "EMP-201",
        "name": "John Doe",
        "department": "Engineering",
        "match_confidence": 0.87,
        "match_distance": 0.32,
        "enrollment_status": "active",
        "face_encoding_count": 5
      },
      "face_attributes": {
        "quality_score": 0.85,
        "is_blurry": false,
        "sharpness": 87.3,
        "brightness": 112,
        "face_size_pixels": 16200,
        "pose": {
          "yaw": 5.2,
          "pitch": -3.1,
          "roll": 1.4
        }
      },
      "snapshot": {
        "url": "https://storage.example.com/faces/det_abc12345.jpg",
        "storage_path": "faces/2025/11/06/det_abc12345.jpg",
        "size_bytes": 45678,
        "format": "jpeg",
        "resolution": "160x160"
      },
      "embedding": null,
      "metadata": {
        "created_at": "2025-11-06T12:45:23.395Z"
      }
    }
  ],
  "summary": {
    "total_detections": 2,
    "identified_persons": 1,
    "unknown_persons": 1,
    "avg_confidence": 0.91
  },
  "model_info": {
    "detection_model": {
      "name": "RetinaFace-MobileNet",
      "version": "1.2.0",
      "device": "GPU-0",
      "latency_ms": 78
    },
    "recognition_model": {
      "name": "ArcFace-ResNet50",
      "version": "2.0.1",
      "embedding_size": 512,
      "device": "GPU-0",
      "latency_ms": 15
    },
    "fallback_used": false
  }
}
```

### 5.2 Error & Edge Cases

#### 5.2.1 No Faces Detected
```json
{
  "status": "success",
  "message": "No faces detected in frame",
  "processing_info": { },
  "detections": [],
  "summary": {
    "total_detections": 0,
    "identified_persons": 0,
    "unknown_persons": 0
  }
}
```

#### 5.2.2 Stream Lost / Camera Disconnected
```json
{
  "status": "error",
  "error": {
    "code": "STREAM_UNAVAILABLE",
    "message": "Camera stream lost. Attempting reconnection.",
    "camera_id": "cam_550e8400-e29b-41d4-a716-446655440000",
    "camera_name": "Main Entrance",
    "last_frame_at": "2025-11-06T12:45:00.000Z",
    "reconnection_attempts": 3,
    "next_retry_at": "2025-11-06T12:45:35.000Z"
  }
}
```

#### 5.2.3 Model Failure / Timeout
```json
{
  "status": "error",
  "error": {
    "code": "MODEL_TIMEOUT",
    "message": "Detection model exceeded timeout (5000ms). Frame dropped.",
    "frame_id": "frame_12345678",
    "timeout_ms": 5000,
    "fallback_used": true,
    "fallback_model": "CPU-FallbackModel-v1"
  }
}
```

### 5.3 Asynchronous Response

For `async: true` requests, immediate response:
```json
{
  "status": "accepted",
  "message": "Frame queued for processing",
  "job_id": "job_xyz789",
  "frame_id": "frame_12345678",
  "estimated_completion_ms": 2000,
  "queue_position": 15,
  "callback_url": "https://app.example.com/detection-callback"
}
```

Later, callback POST to `callback_url`:
```json
{
  "job_id": "job_xyz789",
  "status": "completed",
  "detections": [ ]
}
```

---

## 6. Multi-Stream & Concurrency

### 6.1 Architecture

```mermaid
graph TB
    subgraph "Stream Manager"
        CR[(Camera Registry<br/>PostgreSQL)]
        SO[Stream Orchestrator<br/>- Load enabled cameras<br/>- Spawn workers<br/>- Monitor health<br/>- Restart failed]
    end

    CR --> SO

    SO --> SW1[StreamWorker<br/>Camera 1<br/>- Connect<br/>- Capture<br/>- Buffer<br/>- Queue]
    SO --> SW2[StreamWorker<br/>Camera 2]
    SO --> SWN[StreamWorker<br/>Camera N]

    SW1 --> UFQ[Unified Frame Queue<br/>Redis/RabbitMQ]
    SW2 --> UFQ
    SWN --> UFQ
```

**Design Principle:** Each camera stream operates independently with isolated state, ensuring one camera's failure doesn't affect others.

### 6.2 Concurrency Strategies

#### 6.2.1 Option A: Async/Await (Python asyncio)

**Pros:** Low overhead, efficient for I/O-bound tasks (network streaming)
**Cons:** GIL limits CPU-bound processing (ML inference)

```mermaid
graph TD
    MEL[Main Event Loop]
    MEL --> CC1[Camera 1 Coroutine]
    MEL --> CC2[Camera 2 Coroutine]
    MEL --> CCN[Camera N Coroutine]
    MEL --> RBC[Result Broadcaster]

    subgraph "Worker Thread Pool"
        DW1[Detection Worker 1<br/>GPU slot 0]
        DW2[Detection Worker 2<br/>GPU slot 1]
        DWM[Detection Worker M<br/>CPU threads]
    end

    CC1 --> DW1
    CC2 --> DW2
    CCN --> DWM
```

#### 6.2.2 Option B: Multiprocessing

**Pros:** True parallelism (bypass GIL), fault isolation
**Cons:** Higher memory overhead, IPC complexity

```mermaid
graph TB
    MP[Main Process<br/>Orchestrator]
    MP --> P1[Process 1<br/>Camera Group A<br/>Cameras 1-5]
    MP --> P2[Process 2<br/>Camera Group B<br/>Cameras 6-10]
    MP --> PN[Process N<br/>Camera Group N]

    P1 --> SQ[Shared Queue<br/>Redis/RabbitMQ]
    P2 --> SQ
    PN --> SQ
```

#### 6.2.3 Option C: Hybrid (Recommended)

**Combine async for I/O + threads for CPU + multiprocessing for scaling**

```mermaid
graph TB
    subgraph "Detection Provider - Hybrid Model"
        subgraph "Main Process"
            FASTAPI[FastAPI Server<br/>Async API endpoints]
            ORCH[Stream Orchestrator<br/>Manage workers]
            WSHUB[WebSocket Hub<br/>Broadcast results]
        end

        subgraph "Worker Process 1 - Cameras 1-10"
            AEL1[Async Event Loop]
            CC1[Camera 1-10<br/>Capture Coroutines]
            FQ1[Frame Queue<br/>asyncio.Queue]
            TP1[Thread Pool<br/>4 threads<br/>Detection GPU-0]

            AEL1 --> CC1
            CC1 --> FQ1
            FQ1 --> TP1
        end

        subgraph "Worker Process 2 - Cameras 11-20"
            AEL2[Async Event Loop]
            CC2[Camera 11-20<br/>Capture Coroutines]
            FQ2[Frame Queue]
            TP2[Thread Pool<br/>Detection GPU-1]

            AEL2 --> CC2
            CC2 --> FQ2
            FQ2 --> TP2
        end

        subgraph "Shared Infrastructure"
            REDIS[(Redis<br/>Queues, Cache, Pub/Sub)]
            POSTGRES[(PostgreSQL<br/>Metadata)]
            MINIO[(MinIO<br/>Snapshots)]
        end

        TP1 --> REDIS
        TP2 --> REDIS
        WSHUB --> REDIS
    end
```

### 6.3 Session Management

**StreamSession Object:**
```json
{
  "session_id": "sess_abc123",
  "camera_id": "cam_001",
  "state": "live",
  "connection": {
    "established_at": "2025-11-06T10:00:00Z",
    "last_heartbeat": "2025-11-06T12:45:23Z",
    "reconnection_count": 2,
    "total_downtime_seconds": 45
  },
  "statistics": {
    "frames_captured": 54000,
    "frames_queued": 10800,
    "frames_processed": 10650,
    "frames_dropped": 150,
    "detections_found": 823,
    "avg_fps": 24.8,
    "avg_latency_ms": 145
  },
  "health": {
    "is_healthy": true,
    "last_error": null,
    "error_count": 0,
    "bandwidth_mbps": 3.2,
    "cpu_usage_percent": 12.5
  },
  "subscribers": [
    "ws_client_12345",
    "ws_client_67890"
  ]
}
```

**Session Lifecycle:**

```mermaid
stateDiagram-v2
    [*] --> Connecting: Camera enabled
    Connecting --> Live: Connection established
    Live --> Error: Connection lost
    Error --> Connecting: Retry
    Error --> Stopped: Max retries exceeded
    Live --> Stopped: Camera disabled
    Stopped --> [*]

    note right of Connecting
        Spawn StreamWorker
        Create StreamSession
        Emit: camera_connecting
    end note

    note right of Live
        Normal operation
        Update statistics
        Send heartbeats
    end note

    note right of Error
        Exponential backoff
        Increment retry count
        Emit: camera_error
    end note
```

### 6.4 Resource Allocation

**GPU Resource Management:**
```json
{
  "gpu_pool": {
    "devices": [
      {
        "device_id": 0,
        "device_name": "NVIDIA RTX 4090",
        "memory_total_mb": 24576,
        "memory_available_mb": 18432,
        "max_concurrent_jobs": 4,
        "current_jobs": 2,
        "assigned_cameras": ["cam_001", "cam_002", "cam_003"]
      },
      {
        "device_id": 1,
        "device_name": "NVIDIA RTX 3080",
        "memory_total_mb": 10240,
        "memory_available_mb": 7680,
        "max_concurrent_jobs": 2,
        "current_jobs": 1,
        "assigned_cameras": ["cam_004", "cam_005"]
      }
    ]
  },
  "cpu_pool": {
    "max_workers": 8,
    "current_jobs": 3,
    "queue_size": 15
  }
}
```

**Admission Control:**
```
def can_accept_frame(priority):
  if priority == "urgent":
    return True  # Always accept urgent frames

  if gpu_pool.utilization() > 0.9 and cpu_pool.utilization() > 0.9:
    if priority == "low":
      return False  # Drop low-priority frames under load

  if frame_queue.size() > 1000:
    return False  # Protect against queue overflow

  return True
```

---

## 7. Model Management & Fallback

### 7.1 Model Selection

**Model Registry:**
```json
{
  "detection_models": [
    {
      "model_id": "retinaface-gpu",
      "name": "RetinaFace-MobileNet-GPU",
      "type": "face-detection",
      "device": "cuda:0",
      "priority": 1,
      "latency_p50_ms": 45,
      "latency_p99_ms": 78,
      "throughput_fps": 120,
      "accuracy_map": 0.92,
      "memory_mb": 512,
      "min_face_size": 40,
      "max_batch_size": 8,
      "is_available": true
    },
    {
      "model_id": "yolo-face-cpu",
      "name": "YOLO-Face-CPU",
      "type": "face-detection",
      "device": "cpu",
      "priority": 2,
      "latency_p50_ms": 280,
      "throughput_fps": 18,
      "is_available": true
    }
  ],
  "recognition_models": [
    {
      "model_id": "arcface-512d-gpu",
      "name": "ArcFace-ResNet50-512D",
      "type": "face-recognition",
      "device": "cuda:0",
      "priority": 1,
      "embedding_size": 512,
      "latency_p50_ms": 15,
      "accuracy_lfw": 0.9965,
      "is_available": true
    }
  ]
}
```

### 7.2 GPU vs CPU Mode

**Decision Matrix:**

| Condition | Selected Device | Rationale |
|-----------|----------------|-----------|
| GPU available + utilization < 70% | GPU | Best performance |
| GPU available + utilization > 90% | CPU | Prevent GPU overload |
| GPU unavailable | CPU | Only option |
| Priority = urgent | GPU (forced) | SLA requirement |
| Priority = low | CPU | Save GPU for high-priority |
| Batch size > 4 | GPU | GPU excels at batching |
| Batch size = 1 | CPU | Lower overhead |

### 7.3 Fallback Chain

```mermaid
flowchart TD
    Start[Process Frame] --> Try1[Primary Model<br/>GPU-Based<br/>Timeout: 5s]
    Try1 -->|Success| Done[Return Result]
    Try1 -->|Timeout/Error| Try2[Secondary Model<br/>CPU-Based<br/>Timeout: 10s]
    Try2 -->|Success| Done
    Try2 -->|Timeout/Error| Try3[Tertiary Model<br/>Cloud API<br/>Timeout: 30s]
    Try3 -->|Success| Done
    Try3 -->|Timeout/Error| Fail[Return Error<br/>All models failed]
```

**Fallback Execution Flow:**
```
def process_frame_with_fallback(frame, config):
  fallback_chain = [
    ("retinaface-gpu", 5000),
    ("yolo-face-cpu", 10000),
    ("aws-rekognition", 30000)
  ]

  for model_id, timeout_ms in fallback_chain:
    try:
      model = get_model(model_id)
      if not model.is_available:
        continue

      result = model.detect(frame, timeout=timeout_ms)

      if result.status == "success":
        return {
          "status": "success",
          "detections": result.detections,
          "model_used": model_id,
          "fallback_used": model_id != fallback_chain[0][0]
        }
    except TimeoutError:
      mark_model_degraded(model_id)
      continue
    except Exception:
      mark_model_failed(model_id)
      continue

  return {"status": "error", "error": "All detection models failed"}
```

### 7.4 Performance Optimization

**Warm-up Strategy:**
```
On service startup:
1. Load all configured models into memory
2. Run warm-up inference on dummy frames (10 iterations)
3. Measure latency and mark models as ready
4. Start accepting real traffic only after warm-up completes
```

**Batch Processing:**
```
BatchProcessor:
  max_batch_size: 8
  max_wait_ms: 100

  async def process():
    batch = []
    deadline = now() + max_wait_ms

    while len(batch) < max_batch_size and now() < deadline:
      frame = await frame_queue.get(timeout=10ms)
      batch.append(frame)

    if batch:
      results = model.detect_batch(batch)
      for frame, result in zip(batch, results):
        deliver_result(frame, result)
```

---

## 8. Logging & Audit Trail

### 8.1 Event Types

#### 8.1.1 Detection Events
```json
{
  "event_type": "detection",
  "event_id": "evt_abc123",
  "timestamp": "2025-11-06T12:45:23.395Z",
  "camera_id": "cam_001",
  "camera_name": "Main Entrance",
  "frame_id": "frame_12345678",
  "detections": [
    {
      "detection_id": "det_abc12345",
      "person_id": "per_201",
      "person_name": "John Doe",
      "confidence": 0.93,
      "bounding_box": [120, 85, 240, 220]
    }
  ],
  "processing_time_ms": 127,
  "model_used": "retinaface-gpu"
}
```

#### 8.1.2 Camera Events
```json
{
  "event_type": "camera_connection",
  "event_id": "evt_xyz789",
  "timestamp": "2025-11-06T10:00:15.000Z",
  "camera_id": "cam_001",
  "camera_name": "Main Entrance",
  "status": "connected",
  "connection_attempt": 1,
  "latency_ms": 45,
  "details": "RTSP connection established successfully"
}
```

#### 8.1.3 Model Events
```json
{
  "event_type": "model_fallback",
  "event_id": "evt_model123",
  "timestamp": "2025-11-06T12:45:23.500Z",
  "frame_id": "frame_12345678",
  "primary_model": "retinaface-gpu",
  "fallback_model": "yolo-face-cpu",
  "reason": "timeout",
  "severity": "warning"
}
```

### 8.2 Storage Strategy

**Multi-Tier Logging:**

```mermaid
graph LR
    subgraph "Hot Logs - 24 hours"
        REDIS[Redis Streams<br/>Real-time access<br/>Max 10,000 entries<br/>TTL: 24h]
    end

    subgraph "Warm Logs - 30 days"
        POSTGRES[PostgreSQL<br/>Structured queries<br/>Indexed & partitioned<br/>Analytics ready]
    end

    subgraph "Cold Logs - 1 year"
        S3[MinIO/S3<br/>Compressed JSON<br/>gzip archives<br/>Long-term retention]
    end

    Events --> REDIS
    REDIS --> POSTGRES
    POSTGRES --> S3
```

**Log Entry Schema (PostgreSQL):**
```sql
CREATE TABLE detection_event_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type VARCHAR(50) NOT NULL,
  event_id VARCHAR(100) UNIQUE NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL,
  camera_id UUID REFERENCES cameras(id),
  frame_id VARCHAR(100),
  detection_id UUID REFERENCES detections(id),
  severity VARCHAR(20),
  message TEXT,
  metadata JSONB,
  processing_time_ms INTEGER,
  model_used VARCHAR(100),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_event_log_timestamp ON detection_event_log(timestamp DESC);
CREATE INDEX idx_event_log_camera ON detection_event_log(camera_id, timestamp DESC);
```

### 8.3 Log Entry Structure

**Comprehensive Log Entry:**
```json
{
  "log_id": "log_abc123xyz",
  "timestamp": "2025-11-06T12:45:23.395Z",
  "level": "INFO",
  "event_type": "detection_completed",
  "service": "detection-provider",
  "version": "1.2.0",
  "instance_id": "dp-worker-01",
  "trace_id": "trace_xyz789",
  "span_id": "span_abc123",
  "camera": {
    "camera_id": "cam_001",
    "camera_name": "Main Entrance",
    "location": "HQ Building - Lobby"
  },
  "frame": {
    "frame_id": "frame_12345678",
    "sequence_number": 12345678,
    "timestamp": "2025-11-06T12:45:23.123Z"
  },
  "processing": {
    "queue_time_ms": 34,
    "detection_time_ms": 78,
    "recognition_time_ms": 15,
    "total_time_ms": 127,
    "model_used": "retinaface-gpu",
    "device": "cuda:0"
  },
  "results": {
    "detections_count": 2,
    "identified_count": 1,
    "unknown_count": 1,
    "avg_confidence": 0.91
  },
  "metadata": {
    "fallback_used": false,
    "retry_count": 0
  }
}
```

### 8.4 Audit Trail Requirements

**Regulatory Compliance (GDPR, CCPA):**

1. **Access Logging**
```json
{
  "audit_type": "data_access",
  "timestamp": "2025-11-06T13:00:00.000Z",
  "user_id": "user_admin_01",
  "action": "view_detection",
  "resource": "detection:det_abc12345",
  "person_id": "per_201",
  "ip_address": "192.168.1.50",
  "result": "success"
}
```

2. **Data Modification Logging**
```json
{
  "audit_type": "data_modification",
  "timestamp": "2025-11-06T13:05:00.000Z",
  "user_id": "user_admin_01",
  "action": "delete_detection",
  "resource": "detection:det_abc12345",
  "reason": "User requested data deletion (GDPR)",
  "approval_id": "approval_xyz789"
}
```

3. **Consent Tracking**
```json
{
  "audit_type": "consent",
  "timestamp": "2025-11-06T09:00:00.000Z",
  "person_id": "per_201",
  "consent_type": "face_recognition",
  "status": "granted",
  "expires_at": "2026-11-06T09:00:00.000Z",
  "document_version": "privacy_policy_v2.1"
}
```

---

## 9. Integration with GUI/API

### 9.1 Communication Protocols

#### 9.1.1 REST API (Request-Response)

**Use Case:** One-time queries, configuration updates, historical data retrieval

**Key Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/detections/process-frame` | Submit single frame for detection |
| GET | `/api/v1/detections/live?camera_id={id}` | Get latest detections (cached, 3s TTL) |
| GET | `/api/v1/detections?camera_id={id}&page=1` | Query historical detections |
| GET | `/api/v1/detections/{detection_id}` | Retrieve specific detection |
| POST | `/api/v1/detections/provider/config` | Update provider configuration |
| GET | `/api/v1/detections/statistics?period=1h` | Get aggregated statistics |
| POST | `/api/v1/cameras/{id}/start-detection` | Start continuous detection |
| POST | `/api/v1/cameras/{id}/stop-detection` | Stop continuous detection |

**Example Request:**
```http
GET /api/v1/detections?camera_id=cam_001&start_time=2025-11-06T00:00:00Z&min_confidence=0.7&page=1&page_size=20
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

#### 9.1.2 WebSocket (Real-Time Streaming)

**Use Case:** Live view, real-time alerts, continuous monitoring

**Endpoint:** `ws://api.example.com/api/v1/detections/ws/{client_id}`

**Connection Flow:**

```mermaid
sequenceDiagram
    participant Client
    participant WebSocket Hub
    participant Detection Provider
    participant Redis

    Client->>WebSocket Hub: Connect ws://api.../ws/client_123
    WebSocket Hub->>Client: connection_established
    Client->>WebSocket Hub: subscribe: camera_001
    WebSocket Hub->>Redis: PSUBSCRIBE detection:camera:001
    WebSocket Hub->>Client: subscribed: camera_001

    Detection Provider->>Redis: PUBLISH detection:camera:001
    Redis->>WebSocket Hub: detection_event
    WebSocket Hub->>Client: detection_event (real-time)

    Client->>WebSocket Hub: unsubscribe: camera_001
    WebSocket Hub->>Redis: PUNSUBSCRIBE detection:camera:001
    Client->>WebSocket Hub: disconnect
```

**Message Types:**

**Client → Server:**
```json
{
  "type": "subscribe",
  "camera_id": "cam_001",
  "filters": {
    "min_confidence": 0.7,
    "person_ids": ["per_201", "per_202"]
  }
}
```

**Server → Client:**
```json
{
  "type": "detection_event",
  "timestamp": "2025-11-06T12:45:23.395Z",
  "data": {
    "camera_id": "cam_001",
    "detections": [ ]
  }
}
```

### 9.2 Update Frequency

#### Push Model (Server-Initiated) - **Recommended**

```mermaid
graph LR
    DP[Detection Provider] --> REDIS[Redis Pub/Sub]
    REDIS --> WSHUB[WebSocket Hub]
    WSHUB --> GUI1[GUI Client 1]
    WSHUB --> GUI2[GUI Client 2]
    WSHUB --> GUIN[GUI Client N]
```

**Latency:** 50-100ms from detection completion to GUI display

#### Pull Model (Client-Initiated) - **Fallback**

```mermaid
graph LR
    GUI[GUI Client] --> API[REST API]
    API --> CACHE[Redis Cache<br/>TTL: 3s]
    API --> DB[(PostgreSQL)]
```

**Polling Frequency:** 1-5 seconds
**Latency:** 100-500ms per request

### 9.3 Client Integration Examples

#### 9.3.1 React GUI - WebSocket Integration

**Conceptual Code (Not Actual Implementation):**
```javascript
// WebSocket hook for live detections
function useLiveDetections(cameraId) {
  const [detections, setDetections] = useState([]);
  const ws = useRef(null);

  useEffect(() => {
    ws.current = new WebSocket(`ws://api.example.com/api/v1/detections/ws/client_${userId}`);

    ws.current.onopen = () => {
      ws.current.send(JSON.stringify({
        type: 'subscribe',
        camera_id: cameraId,
        filters: { min_confidence: 0.7 }
      }));
    };

    ws.current.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === 'detection_event') {
        setDetections(prev => [message.data, ...prev].slice(0, 50));
      }
    };

    return () => ws.current.close();
  }, [cameraId]);

  return detections;
}
```

---

## 10. Future Scalability Plan

### 10.1 Horizontal Scaling

**Scaled Architecture (10-1000 Cameras):**

```mermaid
graph TB
    LB[Load Balancer<br/>Nginx/HAProxy/AWS ALB]

    LB --> DP1[Detection Provider 1<br/>Cameras 1-50<br/>GPU-0]
    LB --> DP2[Detection Provider 2<br/>Cameras 51-100<br/>GPU-1]
    LB --> DPN[Detection Provider N<br/>Cameras 451-500<br/>GPU-N]

    DP1 --> MQ[Message Queue<br/>Redis/RabbitMQ]
    DP2 --> MQ
    DPN --> MQ

    MQ --> WSH1[WebSocket Hub 1]
    MQ --> WSHN[WebSocket Hub N]

    WSH1 --> CLIENTS1[GUI Clients]
    WSHN --> CLIENTSN[GUI Clients]

    DP1 --> POSTGRES[(PostgreSQL<br/>Primary + Replicas)]
    DP2 --> POSTGRES
    DPN --> POSTGRES

    DP1 --> REDISCLUSTER[(Redis Cluster)]
    DP2 --> REDISCLUSTER
    DPN --> REDISCLUSTER
```

**Key Changes:**
1. **Camera Assignment:** Consistent hashing on camera_id
2. **Shared State:** Redis Cluster for distributed caching
3. **WebSocket Hub:** Separate service for client connections
4. **Database Scaling:** Primary + read replicas, date-based partitioning

### 10.2 Microservice Decomposition

```mermaid
graph TB
    subgraph "Microservices Architecture"
        CS[Camera Service<br/>- Manage connections<br/>- Extract frames<br/>- Publish to queue]
        FQ[Frame Queue<br/>RabbitMQ/Kafka/Redis]
        DS[Detection Service<br/>- Face detection<br/>- GPU inference<br/>- Emit bounding boxes]
        RS[Recognition Service<br/>- Face encoding<br/>- Embedding comparison<br/>- Person identification]
        AS[Aggregator Service<br/>- Combine results<br/>- Apply business rules<br/>- Generate final output]
        RES[Result Service<br/>- Persist to database<br/>- Upload snapshots<br/>- Broadcast to clients]

        CS --> FQ
        FQ --> DS
        DS --> RS
        RS --> AS
        AS --> RES
    end
```

**Benefits:**
- **Independent Scaling:** Scale detection and recognition separately
- **Technology Flexibility:** Different languages/frameworks per service
- **Fault Isolation:** Failure in one service doesn't crash entire system
- **Deployment Flexibility:** Deploy updates to individual services

### 10.3 Multi-Site Deployment

```mermaid
graph TB
    subgraph "Central Cloud"
        MASTER[(Master DB<br/>PostgreSQL)]
        DASHBOARD[Aggregated<br/>Dashboard]
        GATEWAY[Global API<br/>Gateway]
    end

    subgraph "Site 1 - HQ"
        EDGE1[Edge Node<br/>- Detect<br/>- Recognize<br/>- Local DB]
        CAM1[Cameras 1-20]
        CAM1 --> EDGE1
    end

    subgraph "Site 2 - NYC"
        EDGE2[Edge Node<br/>- Detect<br/>- Recognize<br/>- Local DB]
        CAM2[Cameras 21-40]
        CAM2 --> EDGE2
    end

    subgraph "Site N - LA"
        EDGEN[Edge Node<br/>- Detect<br/>- Recognize<br/>- Local DB]
        CAMN[Cameras 81-100]
        CAMN --> EDGEN
    end

    EDGE1 -.Sync every 5 min.-> GATEWAY
    EDGE2 -.Sync every 5 min.-> GATEWAY
    EDGEN -.Sync every 5 min.-> GATEWAY

    GATEWAY --> MASTER
    MASTER --> DASHBOARD
```

**Edge Computing Model:**
- **Local Processing:** Each site runs its own Detection Provider
- **Local Database:** Site-specific detection records
- **Periodic Sync:** Edge nodes sync to central cloud every 5 minutes
- **Offline Resilience:** Sites continue operating if cloud connection lost

### 10.4 Extension to Other Detection Tasks

**Unified Detection Framework:**

| Detection Type | Use Case | Model Examples |
|----------------|----------|----------------|
| **Face** | Identity, attendance | RetinaFace, ArcFace |
| **Person** | Crowd counting, tracking | YOLO, Faster R-CNN |
| **Vehicle** | Parking, gate access | YOLOv8, License plate OCR |
| **Object** | Security (weapons, bags) | YOLOv8-COCO, Custom models |
| **Activity** | Fall detection, behavior | I3D, SlowFast |

**Multi-Task Processing:**
```json
{
  "detection_tasks": ["face", "vehicle", "object"],
  "results": {
    "faces": [{"person_id": "per_201", "confidence": 0.93}],
    "vehicles": [{"license_plate": "ABC-123", "confidence": 0.88}],
    "objects": [{"class": "backpack", "confidence": 0.76}]
  }
}
```

---

## 11. Implementation Roadmap

### Phase 1: Core Foundation (Weeks 1-4)
- [ ] Implement Camera Service (RTSP + USB support)
- [ ] Build Frame Queue (Redis-based)
- [ ] Integrate Detection Model (single GPU model)
- [ ] Create REST API endpoints
- [ ] Basic database persistence (PostgreSQL)

### Phase 2: Real-Time Streaming (Weeks 5-6)
- [ ] Implement WebSocket Hub
- [ ] Add Redis Pub/Sub for event broadcasting
- [ ] Build live detection cache
- [ ] GUI integration (React components)

### Phase 3: Recognition & Matching (Weeks 7-8)
- [ ] Add Face Recognition Service
- [ ] Implement embedding comparison
- [ ] Build person enrollment workflow
- [ ] Link detections to attendance records

### Phase 4: Resilience & Fallback (Weeks 9-10)
- [ ] Multi-model support
- [ ] Fallback chain implementation
- [ ] Model health monitoring
- [ ] Auto-reconnection for cameras

### Phase 5: Scalability (Weeks 11-12)
- [ ] Load balancer setup
- [ ] Multi-instance deployment
- [ ] Shared state management (Redis Cluster)
- [ ] Performance testing (100+ cameras)

### Phase 6: Advanced Features (Weeks 13-16)
- [ ] Batch processing optimization
- [ ] Multi-site support (edge nodes)
- [ ] Extended detection types (vehicle, object)
- [ ] Advanced analytics dashboard

### Success Metrics

**Performance:**
- Frame processing latency: < 200ms (p95)
- Detection accuracy: > 95% (precision/recall)
- System uptime: > 99.5%
- GPU utilization: 60-80%

**Scalability:**
- Support 100+ concurrent camera streams
- Handle 500+ WebSocket clients
- Process 10,000+ frames/minute

**User Experience:**
- Real-time updates: < 500ms from detection to GUI
- API response time: < 100ms (cached), < 500ms (database)
- Zero missed detections due to system overload

---

## Conclusion

This Detection Provider System Design provides a comprehensive blueprint for implementing an industry-grade face recognition and attendance system. The design is implementation-agnostic, scalable, and ready for any development team to build upon.

**Key Takeaways:**
- ✅ Handles multiple stream types with unified interface
- ✅ Processes frames concurrently with intelligent queuing
- ✅ Delivers real-time results via WebSocket
- ✅ Ensures reliability with multi-model fallback
- ✅ Scales horizontally to 1000+ cameras
- ✅ Maintains comprehensive audit trail for compliance
- ✅ Supports future extensions (vehicles, objects, activities)

**This completes the Detection Provider System Design Document.**

---

**Document Version:** 1.0
**Last Updated:** November 6, 2025
**Maintained By:** System Architecture Team
**License:** Internal Use Only
