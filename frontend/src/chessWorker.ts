self.onmessage = async (e: MessageEvent) => {
  const { fen, timeLimit = 1000, isHint = false } = e.data;
  
  try {
    const response = await fetch('http://localhost:8000/api/move', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ fen, timeLimit, isHint })
    });
    
    if (!response.ok) {
      throw new Error("HTTP Status " + response.status);
    }
    
    const data = await response.json();
    self.postMessage(data);
  } catch (err) {
    console.error("Backend Error:", err);
    self.postMessage({ move: null, message: "Error hitting backend", isHint });
  }
};
