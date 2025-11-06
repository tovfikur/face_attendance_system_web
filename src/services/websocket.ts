/**
 * WebSocket Service
 * Manages real-time connections and event subscriptions
 * Handles auto-reconnection and graceful degradation
 */

export type WebSocketMessageType =
  | 'connection_established'
  | 'initial_status'
  | 'attendance_event'
  | 'person_status_update'
  | 'detection_event'
  | 'ping'
  | 'pong'
  | 'error'

export interface WebSocketMessage {
  type: WebSocketMessageType
  [key: string]: unknown
}

export interface AttendanceEvent extends WebSocketMessage {
  type: 'attendance_event'
  event_timestamp: string
  person_id: string
  person_name: string
  action: 'check_in' | 'check_out'
  timestamp: string
  confidence: number
  attendance_id?: string
  check_in_time?: string
  check_out_time?: string
  duration_minutes?: number
}

export interface PersonStatusUpdate extends WebSocketMessage {
  type: 'person_status_update'
  event_timestamp: string
  person_id: string
  person_name: string
  checked_in: boolean
  check_in_time?: string
  current_duration_minutes?: number
}

export interface DetectionEvent extends WebSocketMessage {
  type: 'detection_event'
  event_timestamp: string
  person_id?: string
  person_name?: string
  camera_id: string
  confidence: number
  face_location?: {
    x: number
    y: number
    width: number
    height: number
  }
}

export type WebSocketEventHandler = (message: WebSocketMessage) => void

class WebSocketService {
  private ws: WebSocket | null = null
  private wsUrl: string
  private clientId: string
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000 // Start with 1 second
  private maxReconnectDelay = 30000 // Max 30 seconds
  private isIntentionallyClosed = false
  private messageHandlers: Map<string, Set<WebSocketEventHandler>> = new Map()
  private connectionPromise: Promise<void> | null = null
  private connectionResolve: (() => void) | null = null

  constructor() {
    const wsBaseUrl =
      import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000'
    this.wsUrl = wsBaseUrl
    this.clientId = `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * Connect to WebSocket endpoint
   */
  connect(
    endpoint: string = '/api/v1/attendance/ws',
    params?: Record<string, string | number | boolean>
  ): Promise<void> {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return Promise.resolve()
    }

    if (this.connectionPromise) {
      return this.connectionPromise
    }

    this.connectionPromise = new Promise((resolve) => {
      this.connectionResolve = resolve
      this.connectInternal(endpoint, params)
    })

    return this.connectionPromise
  }

  private connectInternal(
    endpoint: string,
    params?: Record<string, string | number | boolean>
  ) {
    try {
      this.isIntentionallyClosed = false

      // Build URL
      let url = `${this.wsUrl}${endpoint}/${this.clientId}`
      if (params) {
        const searchParams = new URLSearchParams()
        Object.entries(params).forEach(([key, value]) => {
          searchParams.append(key, String(value))
        })
        url += `?${searchParams.toString()}`
      }

      console.log(`[WebSocket] Connecting to ${url}`)
      this.ws = new WebSocket(url)

      this.ws.onopen = () => {
        console.log('[WebSocket] Connected')
        this.reconnectAttempts = 0
        this.reconnectDelay = 1000
        if (this.connectionResolve) {
          this.connectionResolve()
          this.connectionResolve = null
        }
        this.connectionPromise = null
      }

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage
          this.handleMessage(message)
        } catch (err) {
          console.error('[WebSocket] Failed to parse message:', err)
        }
      }

      this.ws.onerror = (event) => {
        console.error('[WebSocket] Error:', event)
      }

      this.ws.onclose = () => {
        console.log('[WebSocket] Disconnected')
        this.ws = null

        if (!this.isIntentionallyClosed) {
          this.scheduleReconnect(endpoint, params)
        }
      }
    } catch (err) {
      console.error('[WebSocket] Connection error:', err)
      this.scheduleReconnect(endpoint, params)
    }
  }

  private scheduleReconnect(
    endpoint: string,
    params?: Record<string, string | number | boolean>
  ) {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WebSocket] Max reconnection attempts reached')
      if (this.connectionResolve) {
        this.connectionResolve()
        this.connectionResolve = null
      }
      this.connectionPromise = null
      return
    }

    this.reconnectAttempts++
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.maxReconnectDelay
    )

    console.log(
      `[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
    )

    setTimeout(() => {
      if (!this.isIntentionallyClosed) {
        this.connectInternal(endpoint, params)
      }
    }, delay)
  }

  private handleMessage(message: WebSocketMessage) {
    const handlers = this.messageHandlers.get(message.type)
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(message)
        } catch (err) {
          console.error(`[WebSocket] Error in handler for ${message.type}:`, err)
        }
      })
    }

    // Handle ping/pong
    if (message.type === 'ping' && this.ws) {
      try {
        this.ws.send(JSON.stringify({ type: 'pong' }))
      } catch (err) {
        console.error('[WebSocket] Failed to send pong:', err)
      }
    }
  }

  /**
   * Subscribe to message type
   */
  on(messageType: WebSocketMessageType, handler: WebSocketEventHandler): () => void {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, new Set())
    }

    const handlers = this.messageHandlers.get(messageType)!
    handlers.add(handler)

    // Return unsubscribe function
    return () => {
      handlers.delete(handler)
      if (handlers.size === 0) {
        this.messageHandlers.delete(messageType)
      }
    }
  }

  /**
   * Subscribe to attendance events
   */
  onAttendanceEvent(handler: (event: AttendanceEvent) => void): () => void {
    return this.on('attendance_event', handler as WebSocketEventHandler)
  }

  /**
   * Subscribe to detection events
   */
  onDetectionEvent(handler: (event: DetectionEvent) => void): () => void {
    return this.on('detection_event', handler as WebSocketEventHandler)
  }

  /**
   * Subscribe to person status updates
   */
  onPersonStatusUpdate(handler: (event: PersonStatusUpdate) => void): () => void {
    return this.on('person_status_update', handler as WebSocketEventHandler)
  }

  /**
   * Send message to server
   */
  send(message: Record<string, unknown>): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('[WebSocket] WebSocket is not connected')
      return
    }

    try {
      this.ws.send(JSON.stringify(message))
    } catch (err) {
      console.error('[WebSocket] Failed to send message:', err)
    }
  }

  /**
   * Subscribe to different person or filter
   */
  subscribe(personId?: string, minConfidence: number = 0.0): void {
    this.send({
      type: 'subscribe',
      person_id: personId,
      min_confidence: minConfidence,
    })
  }

  /**
   * Unsubscribe and close connection
   */
  disconnect(): void {
    this.isIntentionallyClosed = true
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.messageHandlers.clear()
  }

  /**
   * Get connection status
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }

  /**
   * Get connection state
   */
  getState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED
  }
}

// Singleton instance
let websocketInstance: WebSocketService | null = null

export const getWebSocketService = (): WebSocketService => {
  if (!websocketInstance) {
    websocketInstance = new WebSocketService()
  }
  return websocketInstance
}

export default WebSocketService
