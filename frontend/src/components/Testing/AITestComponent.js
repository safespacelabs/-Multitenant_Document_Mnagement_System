import React, { useState } from 'react';
import { Bot, Brain, Zap, AlertTriangle } from 'lucide-react';

const AITestComponent = () => {
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState(null);

  const testAIProcessing = async () => {
    setProcessing(true);
    try {
      // Test with a sample document ID - replace with actual document ID
      const documentId = 'YOUR_DOCUMENT_ID_HERE';
      
      const response = await fetch(`/api/documents/${documentId}/process-ai`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      setResult(data);
      
      if (response.ok) {
        alert('AI Processing successful! Check console for details.');
        console.log('AI Processing Result:', data);
      } else {
        alert(`Error: ${data.detail}`);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to process document with AI');
    } finally {
      setProcessing(false);
    }
  };

  const checkAIAnalysis = async () => {
    try {
      // Test with a sample document ID - replace with actual document ID
      const documentId = 'YOUR_DOCUMENT_ID_HERE';
      
      const response = await fetch(`/api/documents/${documentId}/ai-analysis`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      const data = await response.json();
      setResult(data);
      
      console.log('AI Analysis Result:', data);
      alert('AI Analysis loaded! Check console for details.');
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to check AI analysis');
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
        <Bot className="h-6 w-6 mr-2 text-purple-600" />
        AI Document Processing Test
      </h2>
      
      <div className="space-y-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="text-lg font-medium text-blue-900 mb-2">Instructions:</h3>
          <ol className="list-decimal list-inside text-sm text-blue-800 space-y-1">
            <li>Replace 'YOUR_DOCUMENT_ID_HERE' with an actual document ID from your system</li>
            <li>Make sure you're logged in and have a valid token</li>
            <li>Click "Process with AI" to test the AI processing endpoint</li>
            <li>Click "Check AI Analysis" to test the analysis retrieval endpoint</li>
            <li>Check the browser console for detailed results</li>
          </ol>
        </div>

        <div className="flex space-x-4">
          <button
            onClick={testAIProcessing}
            disabled={processing}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50"
          >
            {processing ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Processing...
              </>
            ) : (
              <>
                <Zap className="h-4 w-4 mr-2" />
                Process with AI
              </>
            )}
          </button>

          <button
            onClick={checkAIAnalysis}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <Brain className="h-4 w-4 mr-2" />
            Check AI Analysis
          </button>
        </div>

        {result && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h3 className="text-lg font-medium text-gray-900 mb-3 flex items-center">
              <Brain className="h-5 w-5 mr-2 text-indigo-600" />
              Result:
            </h3>
            <pre className="text-sm bg-white p-3 rounded border overflow-auto max-h-64">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default AITestComponent;
