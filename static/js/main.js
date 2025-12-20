let currentMode = 'variation';

function setMode(mode) {
    currentMode = mode;

    // Update UI buttons
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.mode === mode) {
            btn.classList.add('active');
        }
    });

    // Show/Hide Reference Image input
    const refContainer = document.getElementById('refImageContainer');
    const refInput = document.getElementById('refImage');

    if (mode === 'modification') {
        refContainer.style.display = 'block';
        refInput.required = true;
    } else {
        refContainer.style.display = 'none';
        refInput.required = false;
        refInput.value = ''; // Clear value
        // Reset preview to placeholder
        document.getElementById('refPreview').innerHTML = '<span class="placeholder-text">上傳您想模仿的手勢圖片</span>';
    }
}

function previewImage(input, previewId) {
    const previewBox = document.getElementById(previewId);

    if (input.files && input.files[0]) {
        const reader = new FileReader();

        reader.onload = function (e) {
            previewBox.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
        }

        reader.readAsDataURL(input.files[0]);
    } else {
        // Reset to default placeholder based on ID
        let placeholderText = '';
        if (previewId === 'seedPreview') {
            placeholderText = '點擊或拖曳上傳<br>建議尺寸: 320x180 (灰階)';
        } else {
            placeholderText = '上傳您想模仿的手勢圖片';
        }
        previewBox.innerHTML = `<span class="placeholder-text">${placeholderText}</span>`;
    }
}

document.getElementById('generateForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const btn = document.getElementById('generateBtn');
    const originalText = btn.innerText;
    btn.disabled = true;
    btn.innerText = '生成中... ⏳';

    const formData = new FormData();
    formData.append('api_key', document.getElementById('apiKey').value);
    formData.append('model_name', document.getElementById('modelName').value);
    formData.append('prompt', document.getElementById('prompt').value);
    formData.append('mode', currentMode);
    formData.append('batch_size', document.getElementById('batchSize').value);
    formData.append('seed_image', document.getElementById('seedImage').files[0]);

    if (currentMode === 'modification') {
        formData.append('reference_image', document.getElementById('refImage').files[0]);
    }

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const data = await response.json();

            if (data.images && Array.isArray(data.images)) {
                // Process each image in the batch
                data.images.forEach((imgDataUrl, index) => {
                    // Generate filename
                    const timestamp = new Date().toISOString().replace(/[-:T.]/g, '').slice(0, 14);
                    const modeShort = currentMode === 'modification' ? 'mod' : 'var';
                    const promptText = document.getElementById('prompt').value;
                    // Sanitize prompt
                    const promptSnippet = promptText.split(' ').slice(0, 3).join('_').replace(/[^a-zA-Z0-9_]/g, '');
                    const filename = `gesture_${modeShort}_${timestamp}_${promptSnippet || 'gen'}_${index + 1}.png`;

                    addToGallery(imgDataUrl, filename);
                });

                // Remove empty state if it exists
                const emptyState = document.querySelector('.empty-state');
                if (emptyState) {
                    emptyState.remove();
                }
            } else {
                alert('錯誤: 伺服器回傳格式不正確');
            }
        } else {
            const errorData = await response.json();
            alert('錯誤: ' + (errorData.error || '發生未知錯誤'));
        }
    } catch (error) {
        alert('網路錯誤: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.innerText = originalText;
    }
});

function addToGallery(imageUrl, filename = 'generated_gesture.png') {
    const gallery = document.getElementById('gallery');
    const item = document.createElement('div');
    item.className = 'gallery-item';

    // Create a unique ID for this item to reference later if needed
    const itemId = 'img-' + Date.now() + Math.random().toString(36).substr(2, 9);
    item.id = itemId;

    item.innerHTML = `
        <img src="${imageUrl}" alt="Generated Image">
        <div class="actions">
            <button class="analyze-btn" onclick="analyzeImage('${imageUrl}', '${itemId}')">🔍 AI 分析</button>
            <a href="${imageUrl}" download="${filename}" class="download-btn">下載圖片 ⬇️</a>
        </div>
    `;

    gallery.prepend(item);
}

async function analyzeImage(imageUrl, itemId) {
    const item = document.getElementById(itemId);
    if (!item) return;

    // Check if already analyzing or analyzed
    if (item.querySelector('.loading-overlay') || item.querySelector('.analysis-overlay')) {
        return;
    }

    // Show loading state
    const loading = document.createElement('div');
    loading.className = 'loading-overlay';
    loading.innerHTML = 'AI 分析中...';
    item.appendChild(loading);

    try {
        // Convert URL to Blob
        const response = await fetch(imageUrl);
        const blob = await response.blob();

        const formData = new FormData();
        formData.append('api_key', document.getElementById('apiKey').value);
        formData.append('image', blob, 'image.png');

        const apiResponse = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });

        const result = await apiResponse.json();

        // Remove loading
        loading.remove();

        if (apiResponse.ok) {
            showAnalysisResult(item, result);
        } else {
            alert('分析失敗: ' + (result.error || '未知錯誤'));
        }

    } catch (error) {
        loading.remove();
        alert('分析錯誤: ' + error.message);
    }
}

function showAnalysisResult(container, result) {
    const overlay = document.createElement('div');
    overlay.className = 'analysis-overlay';

    // Determine score color
    let scoreClass = 'score-low';
    if (result.realismScore >= 8) scoreClass = 'score-high';
    else if (result.realismScore >= 5) scoreClass = 'score-med';

    overlay.innerHTML = `
        <div class="analysis-header">
            <h4>AI 品質分析報告</h4>
            <button class="close-btn" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
        <div class="analysis-content">
            <div class="analysis-item">
                <span class="analysis-label">手指數量:</span>
                <span class="analysis-value">${result.fingerCount}</span>
            </div>
            <div class="analysis-item">
                <span class="analysis-label">真實度:</span>
                <span class="analysis-value ${scoreClass}">${result.realismScore}/10</span>
            </div>
            <div class="analysis-item">
                <span class="analysis-label">光照:</span>
                <span class="analysis-value">${result.lighting}</span>
            </div>
            <div class="analysis-item">
                <span class="analysis-label">潛在問題:</span>
                <span class="analysis-value" style="color: ${result.issues && result.issues !== 'None' ? '#ff5252' : '#03dac6'}">
                    ${result.issues || '無'}
                </span>
            </div>
        </div>
    `;

    container.appendChild(overlay);
}
