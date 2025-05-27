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
  sender: 'user' | 'bot';
  timestamp: Date;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: 'Hello! How can I help you today?',
      sender: 'bot',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');

  const handleSendMessage = () => {
    if (input.trim() === '') return;
    
    const newUserMessage: Message = {
      id: messages.length + 1,
      text: input,
      sender: 'user',
      timestamp: new Date()
    };
    
    setMessages([...messages, newUserMessage]);
    setInput('');
    
    // Simulate bot response
    setTimeout(() => {
      const newBotMessage: Message = {
        id: messages.length + 2,
        text: `I received your message: "${input}"`,
        sender: 'bot',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, newBotMessage]);
    }, 1000);
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
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Chat Application
          </Typography>
        </Toolbar>
      </AppBar>
      
      {/* Compact introduction section */}
      <Container maxWidth="lg" sx={{ py: 2, px: 3 }}>
        <Typography variant="subtitle1" sx={{ 
          mb: 1,
          fontWeight: 'medium',
          color: 'text.secondary'
        }}>
          Welcome to our chat interface. Type a message below to start chatting!
        </Typography>
      </Container>
      
      {/* Chat area with sticky input */}
      <Container maxWidth="lg" sx={{ 
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        height: 'calc(100vh - 128px)', // Adjust based on header and description height
        position: 'relative'
      }}>
        {/* Messages area - scrollable */}
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
              className={`message-container ${message.sender === 'user' ? 'user-message' : 'bot-message'}`}
            >
              <Typography variant="body1">{message.text}</Typography>
              <Typography 
                className={`message-timestamp ${message.sender === 'user' ? 'user-timestamp' : 'bot-timestamp'}`}
              >
                {message.timestamp.toLocaleTimeString()}
              </Typography>
            </Box>
          ))}
        </Box>
        
        {/* Sticky input area */}
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
            />
            <IconButton 
              className="send-button"
              onClick={handleSendMessage}
              disabled={input.trim() === ''}
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