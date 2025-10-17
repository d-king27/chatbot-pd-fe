import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  Box,
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  TextField,
  IconButton,
  Container,
  Chip,
  Stack
} from '@mui/material';
import { Send as SendIcon } from '@mui/icons-material';
import './App.css'; // NOTE: fixed case from './app.css' -> './App.css'

interface Message {
  id: number;
  text: string;
  sender: 'user' | 'bot' | 'loading';
  timestamp: Date;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: 'Hello! Ask me about one of our Brathay properties.',
      sender: 'bot',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const scrollerRef = useRef<HTMLDivElement | null>(null);

  // -------- Persist conversation locally (so users don't lose context on refresh)
  useEffect(() => {
    try {
      const raw = localStorage.getItem('chat.messages');
      if (raw) {
        const parsed: Message[] = JSON.parse(raw).map((m: any) => ({ ...m, timestamp: new Date(m.timestamp) }));
        if (parsed.length) setMessages(parsed);
      }
    } catch {}
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem('chat.messages', JSON.stringify(messages));
    } catch {}
  }, [messages]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    const el = scrollerRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
  }, [messages.length, loading]);

  // Quick suggestions on empty thread
  const suggestions = useMemo(
    () => ['Find availability for next weekend', 'Dog-friendly cottages', 'Compare two properties'],
    []
  );

  const handleSendMessage = async () => {
    if (input.trim() === '') return;

    // Add user message
    const newUserMessage: Message = {
      id: messages.length + 1,
      text: input,
      sender: 'user',
      timestamp: new Date()
    };
    setMessages(prev => [...prev, newUserMessage]);

    const userInput = input; // preserve input
    setInput('');

    // Show typing indicator
    setLoading(true);
    const loadingMessage: Message = {
      id: messages.length + 2,
      text: '…',
      sender: 'loading',
      timestamp: new Date()
    };
    setMessages(prev => [...prev, loadingMessage]);

    // -------- Conversational memory (client): build a compact history array
    // We'll include the last ~8 turns (16 messages) excluding 'loading'
    const memory = [...messages, newUserMessage]
      .filter(m => m.sender !== 'loading')
      .slice(-16)
      .map(m => ({
        role: m.sender === 'user' ? 'user' : 'assistant',
        content: m.text
      }));

    try {
      // NOTE: keep your existing request working right now.
      // NEW: When your backend supports memory, REPLACE the body below with the commented one.
      //
      // --- NEW BODY (enable when ready):
      // body: JSON.stringify({
      //   question: userInput,
      //   history: memory,                  // <-- full conversation snippet
      //   conversation_id: getOrCreateCid() // <-- optional: stable thread id
      // })
      //
      // --- CURRENT BODY (kept for compatibility):
      const response = await fetch('https://chatbot-pd-fe.onrender.com/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userInput })
      });

      const data = await response.json();
      const botReply = data.response || 'Sorry, no response received.';

      // Replace typing indicator with actual response
      setMessages(prev => [
        ...prev.filter(msg => msg.sender !== 'loading'),
        {
          id: prev.length + 1,
          text: botReply,
          sender: 'bot',
          timestamp: new Date()
        }
      ]);
    } catch (error) {
      console.error('Error fetching response:', error);
      setMessages(prev => [
        ...prev.filter(msg => msg.sender !== 'loading'),
        {
          id: prev.length + 1,
          text: 'Error: Unable to reach the chatbot service.',
          sender: 'bot',
          timestamp: new Date()
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Utility: stable conversation id (kept client-side)
  function getOrCreateCid() {
    const key = 'chat.conversation_id';
    let cid = localStorage.getItem(key);
    if (!cid) {
      cid = Math.random().toString(36).slice(2);
      localStorage.setItem(key, cid);
    }
    return cid;
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Box className="chat-app-container">
      <CssBaseline />
      <AppBar position="sticky" elevation={0} className="appbar-blur">
        <Toolbar sx={{ width: '100%', alignItems: 'center', gap: 1, py: 1.25 }}>
          <Box
            sx={{
              width: 28,
              height: 28,
              borderRadius: '50%',
              bgcolor: 'var(--brand-primary)'
            }}
          />
          <Box sx={{ flexGrow: 1, minWidth: 0 }}>
            <Typography
              variant="h6"
              sx={{ fontWeight: 700, color: 'var(--ink)', letterSpacing: 0.2, lineHeight: 1 }}
              noWrap
            >
             GH-DK Chat Bot
            </Typography>
            <Typography variant="caption" sx={{ color: 'var(--muted)' }} noWrap>
              Alpha 2.0
            </Typography>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Intro / suggestions */}
      <Container maxWidth="lg" sx={{ py: 2, px: 3 }}>
        <Typography
          variant="subtitle1"
          sx={{ mb: 1, fontWeight: 500, color: 'var(--muted)' }}
        >
          Ask about dates, availability, or property details.
           {/* I’ll remember what you’ve said in this chat. */}
        </Typography>
      </Container>

      {/* Chat area */}
      <Container
        maxWidth="lg"
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          height: 'calc(100vh - 180px)',
          position: 'relative'
        }}
      >
        <Box ref={scrollerRef} className="chat-scroll">
          {messages.map(message => (
            <Box
              key={message.id}
              className={`message-container ${
                message.sender === 'user'
                  ? 'user-message'
                  : message.sender === 'bot'
                  ? 'bot-message'
                  : 'loading-message'
              }`}
            >
              <Typography variant="body1">
                {message.sender === 'loading' ? 'Thinking…' : message.text}
              </Typography>
              {message.sender !== 'loading' && (
                <Typography
                  className={`message-timestamp ${
                    message.sender === 'user' ? 'user-timestamp' : 'bot-timestamp'
                  }`}
                >
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </Typography>
              )}
            </Box>
          ))}
        </Box>

        {/* Input */}
        <Box
          sx={{
            position: 'sticky',
            bottom: 0,
            backgroundColor: 'transparent',
            paddingTop: '8px',
            borderTop: '1px solid #ececec',
            zIndex: 1
          }}
          className="safe-bottom"
        >
          <Box className="input-area">
            <TextField
              fullWidth
              multiline
              maxRows={5}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message here…"
              variant="outlined"
              className="message-input"
              disabled={loading}
            />
            <IconButton
              className="send-button"
              onClick={handleSendMessage}
              disabled={input.trim() === '' || loading}
              aria-label="Send message"
            >
              <SendIcon />
            </IconButton>
          </Box>
        </Box>
      </Container>
    </Box>
  );
}

export default App;
