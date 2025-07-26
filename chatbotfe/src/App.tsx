import React, { useState } from 'react';
import { 
  Box, 
  CssBaseline, 
  AppBar, 
  Toolbar, 
  Typography, 
  TextField, 
  IconButton,
  Container
} from '@mui/material';
import { Send as SendIcon } from '@mui/icons-material';
import './app.css';

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
      text: 'Hello! ask me about one of Brathay Properties?',
      sender: 'bot',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

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

    // Show "bot is typing" message
    setLoading(true);
    const loadingMessage: Message = {
      id: messages.length + 2,
      text: 'Bot is typing...',
      sender: 'loading',
      timestamp: new Date()
    };
    setMessages(prev => [...prev, loadingMessage]);

    try {
      // Call API
      const response = await fetch('https://chatbot-pd-fe.onrender.com/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userInput })
      });

      const data = await response.json();
      const botReply = data.response || 'Sorry, no response received.';

      // Replace "Bot is typing..." with actual response
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

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Box className="chat-app-container">
      <CssBaseline />
      <AppBar position="static">
        <Toolbar sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Chat Application
          </Typography>
          <Typography variant="caption" sx={{ fontStyle: 'italic', opacity: 0.8 }}>
            Alpha Build
          </Typography>
        </Toolbar>
      </AppBar>
      
      {/* Intro */}
      <Container maxWidth="lg" sx={{ py: 2, px: 3 }}>
        <Typography variant="subtitle1" sx={{ 
          mb: 1,
          fontWeight: 'medium',
          color: 'text.secondary'
        }}>
          Welcome to our chat interface. Type a message below to start chatting!
        </Typography>
      </Container>
      
      {/* Chat area */}
      <Container maxWidth="lg" sx={{ 
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        height: 'calc(100vh - 128px)',
        position: 'relative'
      }}>
        <Box sx={{ 
          flex: 1,
          overflowY: 'auto',
          padding: '16px',
          border: '1px solid #e0e0e0',
          borderRadius: '8px',
          backgroundColor: '#fafafa',
          marginBottom: '16px'
        }}>
          {messages.map((message) => (
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
              <Typography variant="body1">{message.text}</Typography>
              {message.sender !== 'loading' && (
                <Typography 
                  className={`message-timestamp ${
                    message.sender === 'user' ? 'user-timestamp' : 'bot-timestamp'
                  }`}
                >
                  {message.timestamp.toLocaleTimeString()}
                </Typography>
              )}
            </Box>
          ))}
        </Box>
        
        {/* Input */}
        <Box sx={{
          position: 'sticky',
          bottom: 0,
          backgroundColor: 'background.paper',
          padding: '16px 0',
          borderTop: '1px solid #e0e0e0',
          zIndex: 1
        }}>
          <Box className="input-area">
            <TextField
              fullWidth
              multiline
              maxRows={4}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message here..."
              variant="outlined"
              className="message-input"
              disabled={loading}
            />
            <IconButton 
              className="send-button"
              onClick={handleSendMessage}
              disabled={input.trim() === '' || loading}
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
