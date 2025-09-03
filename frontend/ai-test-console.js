// AI Processing Test - Run this in browser console
// Copy and paste this entire code into your browser console

console.log('🤖 AI Processing Test Script Loaded');

// Function to process document with AI
async function processDocumentWithAI(documentId) {
    console.log('🚀 Processing document with AI:', documentId);
    
    try {
        const response = await fetch(`/api/documents/${documentId}/process-ai`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log('📡 Response status:', response.status);
        const result = await response.json();
        console.log('📄 AI Processing Result:', result);
        
        if (response.ok) {
            if (result.already_processed) {
                alert('✅ Document already processed by AI!');
            } else {
                alert('✅ Document processed successfully with AI!');
            }
            return result;
        } else {
            alert(`❌ Error: ${result.detail || 'Unknown error'}`);
            return null;
        }
    } catch (error) {
        console.error('❌ Error:', error);
        alert(`❌ Failed to process document with AI: ${error.message}`);
        return null;
    }
}

// Function to check AI analysis
async function checkAIAnalysis(documentId) {
    console.log('🧠 Checking AI analysis for document:', documentId);
    
    try {
        const response = await fetch(`/api/documents/${documentId}/ai-analysis`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        console.log('📡 Response status:', response.status);
        const result = await response.json();
        console.log('📄 AI Analysis Result:', result);
        
        if (response.ok) {
            if (result.ai_processed) {
                alert('✅ AI Analysis found! Check console for details.');
            } else {
                alert('ℹ️ Document not processed by AI yet.');
            }
            return result;
        } else {
            alert(`❌ Error: ${result.detail || 'Unknown error'}`);
            return null;
        }
    } catch (error) {
        console.error('❌ Error:', error);
        alert(`❌ Failed to check AI analysis: ${error.message}`);
        return null;
    }
}

// Function to get document ID from current page
function getDocumentId() {
    // Try to find document ID from the page
    const documentElements = document.querySelectorAll('[data-document-id]');
    if (documentElements.length > 0) {
        return documentElements[0].getAttribute('data-document-id');
    }
    
    // Try to find from URL or other sources
    const urlParams = new URLSearchParams(window.location.search);
    const docId = urlParams.get('documentId');
    if (docId) return docId;
    
    // Look for document ID in the page content
    const textContent = document.body.textContent;
    const uuidMatch = textContent.match(/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i);
    if (uuidMatch) {
        return uuidMatch[0];
    }
    
    return null;
}

// Main test function
async function testAIProcessing() {
    console.log('🧪 Starting AI Processing Test...');
    
    // Check if we have a token
    const token = localStorage.getItem('access_token');
    if (!token) {
        alert('❌ No access token found. Please log in first.');
        return;
    }
    
    console.log('🔑 Token found:', token.substring(0, 20) + '...');
    
    // Try to get document ID
    let documentId = getDocumentId();
    
    if (!documentId) {
        documentId = prompt('Enter document ID:');
        if (!documentId) {
            alert('❌ No document ID provided.');
            return;
        }
    }
    
    console.log('📄 Document ID:', documentId);
    
    // Test AI processing
    const result = await processDocumentWithAI(documentId);
    
    if (result) {
        // Test AI analysis
        await checkAIAnalysis(documentId);
    }
}

// Add buttons to the page
function addAITestButtons() {
    // Find the document actions area
    const documentActions = document.querySelector('[class*="flex items-center space-x-2"]');
    
    if (documentActions) {
        // Create AI test button
        const aiButton = document.createElement('button');
        aiButton.innerHTML = '🤖 Test AI';
        aiButton.className = 'text-purple-600 hover:text-purple-900 p-1';
        aiButton.title = 'Test AI Processing';
        aiButton.onclick = testAIProcessing;
        
        // Insert before the delete button
        const deleteButton = documentActions.querySelector('[title="Delete document"]');
        if (deleteButton) {
            documentActions.insertBefore(aiButton, deleteButton);
        } else {
            documentActions.appendChild(aiButton);
        }
        
        console.log('✅ AI Test button added to page');
    } else {
        console.log('❌ Could not find document actions area');
    }
}

// Auto-run when script loads
console.log('🎯 AI Processing Test Script Ready!');
console.log('📋 Available functions:');
console.log('  - testAIProcessing() - Run full AI test');
console.log('  - processDocumentWithAI(documentId) - Process specific document');
console.log('  - checkAIAnalysis(documentId) - Check AI analysis');
console.log('  - addAITestButtons() - Add test buttons to page');

// Add buttons automatically
setTimeout(addAITestButtons, 1000);

// Make functions available globally
window.testAIProcessing = testAIProcessing;
window.processDocumentWithAI = processDocumentWithAI;
window.checkAIAnalysis = checkAIAnalysis;
window.addAITestButtons = addAITestButtons;
