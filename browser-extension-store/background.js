// Background Service Worker for ScriptSor Audio Converter
// Handles extension lifecycle and background tasks

console.log('ScriptSor Audio Converter background service worker started');

// Install event
chrome.runtime.onInstalled.addListener((details) => {
    console.log('Extension installed:', details.reason);
    
    if (details.reason === 'install') {
        // Set default settings
        chrome.storage.sync.set({
            conversionQuality: 'high',
            autoUpload: true,
            showNotifications: true
        });
        
        // Open welcome page
        chrome.tabs.create({
            url: chrome.runtime.getURL('welcome.html')
        });
    }
});

// Handle messages from popup or content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    switch (request.action) {
        case 'convertVideo':
            handleVideoConversion(request, sender, sendResponse);
            return true;
            
        case 'uploadToScriptSor':
            handleUploadToScriptSor(request, sender, sendResponse);
            return true;
            
        case 'getSettings':
            getSettings(sendResponse);
            return true;
            
        case 'saveSettings':
            saveSettings(request.settings, sendResponse);
            return true;
    }
});

// Video conversion handler
async function handleVideoConversion(request, sender, sendResponse) {
    try {
        const { videoFile, options } = request;
        
        // Create notification for conversion start
        if (options.showNotifications) {
            chrome.notifications.create({
                type: 'basic',
                iconUrl: 'icons/icon48.png',
                title: 'ScriptSor Converter',
                message: 'Starting video conversion...'
            });
        }
        
        // Simulate conversion progress
        for (let i = 0; i <= 100; i += 10) {
            await new Promise(resolve => setTimeout(resolve, 200));
            
            // Send progress update to popup
            chrome.runtime.sendMessage({
                action: 'conversionProgress',
                progress: i,
                videoId: request.videoId
            });
        }
        
        // Send completion notification
        if (options.showNotifications) {
            chrome.notifications.create({
                type: 'basic',
                iconUrl: 'icons/icon48.png',
                title: 'ScriptSor Converter',
                message: 'Conversion completed successfully!'
            });
        }
        
        sendResponse({ success: true });
    } catch (error) {
        console.error('Conversion error:', error);
        sendResponse({ success: false, error: error.message });
    }
}

// Upload handler
async function handleUploadToScriptSor(request, sender, sendResponse) {
    try {
        const { audioBlob, fileName, videoId } = request;
        
        // Create FormData for upload
        const formData = new FormData();
        const audioFile = new File([audioBlob], fileName, {
            type: 'audio/wav'
        });
        formData.append('file', audioFile);
        
        // Upload to backend
        const response = await fetch('https://scriptssor.onrender.com/upload', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            
            // Open ScriptSor in new tab
            chrome.tabs.create({
                url: `https://scriptssor-frontend.onrender.com/?video_id=${result.video_id}`
            });
            
            sendResponse({ success: true, videoId: result.video_id });
        } else {
            throw new Error('Upload failed');
        }
    } catch (error) {
        console.error('Upload error:', error);
        sendResponse({ success: false, error: error.message });
    }
}

// Settings management
function getSettings(sendResponse) {
    chrome.storage.sync.get([
        'conversionQuality',
        'autoUpload',
        'showNotifications'
    ], (result) => {
        sendResponse({
            conversionQuality: result.conversionQuality || 'high',
            autoUpload: result.autoUpload !== false,
            showNotifications: result.showNotifications !== false
        });
    });
}

function saveSettings(settings, sendResponse) {
    chrome.storage.sync.set(settings, () => {
        sendResponse({ success: true });
    });
}

// Context menu for right-click conversion
chrome.contextMenus.create({
    id: 'convertVideo',
    title: 'Convert video with ScriptSor',
    contexts: ['link', 'video']
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === 'convertVideo') {
        // Handle context menu conversion
        chrome.tabs.sendMessage(tab.id, {
            action: 'contextMenuConvert',
            linkUrl: info.linkUrl,
            videoUrl: info.srcUrl
        });
    }
});

// Storage cleanup on uninstall
chrome.runtime.setUninstallURL('https://scriptssor-frontend.onrender.com/goodbye');

console.log('ScriptSor Audio Converter background service worker ready');