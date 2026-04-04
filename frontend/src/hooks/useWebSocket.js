import { useEffect, useRef, useCallback, useState } from 'react'

// Use environment variable for the URL if possible
const WS_URL = 'ws://localhost:8000/ws/trading-floor'

export function useWebSocket() {
  const wsRef = useRef(null)
  const [status, setStatus] = useState('disconnected')
  const [messages, setMessages] = useState([])
  const [lastMessage, setLastMessage] = useState(null)
  const reconnectTimer = useRef(null)
  
  // Refs for audio to prevent memory leaks and overlapping play
  const currentAudioRef = useRef(null)
  const audioUrlsRef = useRef([])

  const connect = useCallback(() => {
    // 1. Get the latest session ID from storage
    const sessionId = localStorage.getItem('sessionId');
    if (!sessionId) {
      console.error("No Session ID found, skipping connection");
      return;
    }

    // 2. Prevent duplicate connections
    if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) return

    setStatus('connecting')

    // 3. Append session_id to the URL so the backend can fetch the user's ElevenLabs voices
    const ws = new WebSocket(`${WS_URL}?session_id=${sessionId}`)
    wsRef.current = ws

    ws.onopen = () => {
      if (wsRef.current !== ws) return
      setStatus('connected')
      clearTimeout(reconnectTimer.current)
    }

    ws.onmessage = (event) => {
      if (wsRef.current !== ws) return

      try {
        const data = JSON.parse(event.data)
        if (data.type === 'ping') return

        setLastMessage(data)
        setMessages(prev => [...prev, data])

        // --- Efficient Audio Handling ---
        if (data.type === "agent_voice" && data.audio) {
          if (currentAudioRef.current) {
            currentAudioRef.current.pause()
            currentAudioRef.current = null
          }

          // Convert base64 or array buffer to blob
          const audioBlob = new Blob(
            [new Uint8Array(data.audio)],
            { type: "audio/mpeg" }
          )

          const url = URL.createObjectURL(audioBlob)
          audioUrlsRef.current.push(url) // Track for cleanup

          const audio = new Audio(url)
          currentAudioRef.current = audio
          audio.play().catch(err => console.error("Audio block:", err))
        }
      } catch (err) {
        console.error("WS parse error:", err)
      }
    }

    ws.onerror = () => {
      if (wsRef.current !== ws) return
      setStatus('error')
    }

    ws.onclose = () => {
      if (wsRef.current !== ws) return
      setStatus('disconnected')
      wsRef.current = null
      
      // Auto-reconnect logic
      reconnectTimer.current = setTimeout(() => {
        if (document.visibilityState !== 'hidden') connect()
      }, 3000)
    }
  }, [])

  const disconnect = useCallback(() => {
    clearTimeout(reconnectTimer.current)
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setStatus('disconnected')
  }, [])

  const clearMessages = useCallback(() => {
    setMessages([])
    // Clean up all generated Audio URLs to free browser memory
    audioUrlsRef.current.forEach(url => URL.revokeObjectURL(url))
    audioUrlsRef.current = []
  }, [])

  useEffect(() => {
    connect()
    return () => { 
      disconnect()
      // Final memory cleanup
      audioUrlsRef.current.forEach(url => URL.revokeObjectURL(url))
    }
  }, [connect, disconnect])

  return { messages, lastMessage, status, connect, disconnect, clearMessages }
}