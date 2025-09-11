// Content Script for ScriptSor Audio Converter
// This script runs on the ScriptSor web pages

console.log('ScriptSor Audio Converter content script loaded');

// Listen for messages from the extension
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'uploadAudio') {
        // Handle audio file upload from extension
        handleAudioUpload(request.audioBlob, request.fileName);
    }
    
    return true; // Keep the message channel open for async response
});

// Function to handle audio file upload
async function handleAudioUpload(audioBlob, fileName) {
    try {
        // Create a File object from the blob
        const audioFile = new File([audioBlob], fileName, {
            type: 'audio/wav'
        });
        
        // Find the file input on the page
        const fileInput = document.querySelector('input[type="file"]');
        if (fileInput) {
            // Create a DataTransfer object to set the file
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(audioFile);
            fileInput.files = dataTransfer.files;
            
            // Trigger the change event
            const event = new Event('change', { bubbles: true });
            fileInput.dispatchEvent(event);
            
            console.log('Audio file uploaded successfully');
        } else {
            console.error('File input not found on the page');
        }
    } catch (error) {
        console.error('Error handling audio upload:', error);
    }
}

// Add a small indicator to show the extension is active
function addExtensionIndicator() {
    const indicator = document.createElement('div');
    indicator.innerHTML = '🎵 ScriptSor Extension Active';
    indicator.style.cssText = `
        position: fixed;
        top: 10px;
        right: 10px;
        background: rgba(34, 197, 94, 0.9);
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-size: 12px;
        z-index: 9999;
        opacity: 0.8;
    `;
    document.body.appendChild(indicator);
    
    // Hide after 3 seconds
    setTimeout(() => {
        indicator.style.opacity = '0';
        setTimeout(() => {
            document.body.removeChild(indicator);
        }, 300);
    }, 3000);
}

// Show indicator when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addExtensionIndicator);
} else {
    addExtensionIndicator();
}