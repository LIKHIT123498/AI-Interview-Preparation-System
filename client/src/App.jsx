import { useState, useEffect, useRef } from 'react';
import { uploadResumeAndJD } from './services/api';
import { Send, UploadCloud, ShieldAlert, Cpu, Mic, MicOff } from 'lucide-react';
import './App.css';

export default function App() {
  const [step, setStep] = useState('setup'); // 'setup' or 'interview'
  const [userId] = useState(1); // Mock user ID for demo
  const [jobDescription, setJobDescription] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  
  // WebSocket State
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const ws = useRef(null);
  const chatBottomRef = useRef(null);

  // Speech-to-text state
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef(null);
  const speechBaseTextRef = useRef('');

  // Initialize the browser's native speech recognition when available.
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      return undefined;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        transcript += event.results[i][0].transcript;
      }

      setInputMessage(`${speechBaseTextRef.current}${transcript}`);
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error', event.error);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.stop();
      recognitionRef.current = null;
    };
  }, []);

  const toggleListening = () => {
    if (!recognitionRef.current) {
      alert('Speech recognition is not supported in this browser. Try Google Chrome or Microsoft Edge.');
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
      return;
    }

    speechBaseTextRef.current = inputMessage.trim()
      ? `${inputMessage.trim()} `
      : '';
    recognitionRef.current.start();
    setIsListening(true);
  };

  // Handle Resume Upload & Start Interview Setup
  const handleStartInterview = async (e) => {
    e.preventDefault();
    if (!file || !jobDescription) {
      alert("Please provide both a resume PDF and a Job Description.");
      return;
    }

    setLoading(true);
    try {
      const data = await uploadResumeAndJD(userId, jobDescription, file);
      setAnalysisResult(data.analysis);
      
      // For demonstration, assume session ID 1 was created in DB
      // In production, your FastAPI /analyze-resume endpoint will return a session_id
      setSessionId(1); 
      setStep('interview');
    } catch (err) {
      console.error(err);
      alert("Failed to process resume. Ensure backend is running.");
    } finally {
      setLoading(false);
    }
  };

  // Setup WebSocket connection when entering the interview step
  useEffect(() => {
    if (step === 'interview' && sessionId) {
      ws.current = new WebSocket(`ws://localhost:8000/ws/interview/${sessionId}`);

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setMessages((prev) => [...prev, { sender: 'AI', text: data.message }]);
      };

      ws.current.onclose = () => {
        console.log("WebSocket connection closed.");
      };

      return () => {
        if (ws.current) ws.current.close();
      };
    }
  }, [step, sessionId]);

  // Auto-scroll chat window
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Send message through WebSocket
  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || !ws.current) return;

    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }

    const userText = inputMessage;
    setMessages((prev) => [...prev, { sender: 'You', text: userText }]);
    ws.current.send(userText);
    setInputMessage('');
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1><Cpu className="icon" /> AI Interview Prep Studio</h1>
        <p>Rigorous, context-aware cross-examination powered by FastAPI & Gemini</p>
      </header>

      {step === 'setup' ? (
        <div className="setup-card">
          <h2>Step 1: Role & Resume Configuration</h2>
          <form onSubmit={handleStartInterview}>
            <div className="form-group">
              <label>Target Job Description</label>
              <textarea 
                rows="5"
                placeholder="Paste the target job description here..."
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label>Upload Resume (PDF)</label>
              <div className="file-dropzone">
                <UploadCloud size={32} />
                <input 
                  type="file" 
                  accept=".pdf"
                  onChange={(e) => setFile(e.target.files[0])}
                  required
                />
                <span>{file ? file.name : "Choose PDF or drag & drop"}</span>
              </div>
            </div>

            <button type="submit" className="primary-btn" disabled={loading}>
              {loading ? "Analyzing Resume & Gaps..." : "Initialize Interview Track"}
            </button>
          </form>
        </div>
      ) : (
        <div className="interview-container">
          <div className="sidebar-panel">
            <h3>Target Alignment</h3>
            {analysisResult && (
              <div className="insights-box">
                <div className="score-badge">
                  Readiness Score: <span>{analysisResult.readiness_score}/100</span>
                </div>
                <h4>Identified Gaps to Probe:</h4>
                <ul>
                  {analysisResult.identified_gaps?.map((gap, i) => (
                    <li key={i}><ShieldAlert size={14} /> {gap}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className="chat-panel">
            <div className="chat-messages">
              {messages.map((msg, index) => (
                <div key={index} className={`message ${msg.sender === 'AI' ? 'ai-msg' : 'user-msg'}`}>
                  <strong>{msg.sender}:</strong>
                  <p>{msg.text}</p>
                </div>
              ))}
              <div ref={chatBottomRef} />
            </div>

            <form onSubmit={handleSendMessage} className="chat-input-form">
              <button
                type="button"
                onClick={toggleListening}
                className={`mic-btn ${isListening ? 'listening' : ''}`}
                title={isListening ? 'Stop listening' : 'Start voice input'}
                aria-label={isListening ? 'Stop listening' : 'Start voice input'}
              >
                {isListening ? <MicOff size={18} color="#f87171" /> : <Mic size={18} />}
              </button>
              <input 
                type="text"
                placeholder={isListening
                  ? 'Listening... Speak your answer now...'
                  : 'Type or click mic to speak your answer...'}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                autoComplete="off"
              />
              <button type="submit" className="send-btn"><Send size={18} /></button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}