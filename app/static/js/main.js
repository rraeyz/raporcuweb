// RaporcuWeb JavaScript Functions

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(function(card, index) {
        card.style.animationDelay = (index * 0.1) + 's';
        card.classList.add('fade-in');
    });
    
    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Bu işlemi gerçekleştirmek istediğinizden emin misiniz?')) {
                e.preventDefault();
            }
        });
    });
    
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // Tooltip initialization
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Popover initialization
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// Copy to clipboard function
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showToast('Panoya kopyalandı!', 'success');
    }, function(err) {
        showToast('Kopyalama başarısız!', 'danger');
    });
}

// Show toast notification
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.getElementById('toastContainer').appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// Handle file upload
function handleFileUpload(input) {
    const file = input.files[0];
    if (file) {
        const fileInfo = document.getElementById('file-info');
        const fileName = document.getElementById('file-name');
        fileName.textContent = file.name + ' (' + formatFileSize(file.size) + ')';
        fileInfo.classList.remove('d-none');
        showToast('Dosya yüklendi: ' + file.name, 'success');
    }
}

// Clear uploaded file
function clearFile() {
    const fileInput = document.getElementById('file_upload');
    const fileInfo = document.getElementById('file-info');
    fileInput.value = '';
    fileInfo.classList.add('d-none');
    showToast('Dosya kaldırıldı', 'info');
}

// Handle audio file upload
function handleAudioUpload(input) {
    const file = input.files[0];
    if (file) {
        const audioInfo = document.getElementById('audio-info');
        const audioName = document.getElementById('audio-name');
        audioName.textContent = file.name + ' (' + formatFileSize(file.size) + ')';
        audioInfo.classList.remove('d-none');
        showToast('Ses dosyası yüklendi: ' + file.name, 'success');
    }
}

// Clear audio file
function clearAudio() {
    const audioInput = document.getElementById('audio_upload');
    const audioInfo = document.getElementById('audio-info');
    audioInput.value = '';
    audioInfo.classList.add('d-none');
    showToast('Ses dosyası kaldırıldı', 'info');
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Format number with thousands separator
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

// Format currency
function formatCurrency(amount, currency = 'TL') {
    return new Intl.NumberFormat('tr-TR', {
        style: 'currency',
        currency: 'TRY',
        minimumFractionDigits: 2
    }).format(amount).replace('₺', currency);
}

// Loading state for buttons
function setButtonLoading(button, loading = true) {
    if (loading) {
        button.dataset.originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Yükleniyor...';
    } else {
        button.disabled = false;
        button.innerHTML = button.dataset.originalText || button.innerHTML;
    }
}

// AJAX helper function
async function fetchAPI(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showToast('Bir hata oluştu. Lütfen tekrar deneyin.', 'danger');
        throw error;
    }
}

// Debounce function for search inputs
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Smooth scroll to element
function smoothScrollTo(element) {
    element.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    });
}

// Check if element is in viewport
function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

// Local storage helpers
const storage = {
    set: function(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
            console.error('LocalStorage Error:', e);
            return false;
        }
    },
    get: function(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.error('LocalStorage Error:', e);
            return defaultValue;
        }
    },
    remove: function(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            console.error('LocalStorage Error:', e);
            return false;
        }
    }
};

// Audio Recording
let mediaRecorder;
let audioChunks = [];
let recordingStartTime;
let timerInterval;

// Toggle between record and upload modes
document.addEventListener('DOMContentLoaded', function() {
    const recordOption = document.getElementById('audio_record');
    const fileOption = document.getElementById('audio_file');
    const recordingSection = document.getElementById('recording-section');
    const uploadSection = document.getElementById('upload-section');
    
    if (recordOption && fileOption) {
        recordOption.addEventListener('change', function() {
            if (recordingSection) recordingSection.classList.remove('d-none');
            if (uploadSection) uploadSection.classList.add('d-none');
        });
        
        fileOption.addEventListener('change', function() {
            if (recordingSection) recordingSection.classList.add('d-none');
            if (uploadSection) uploadSection.classList.remove('d-none');
        });
    }
});

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            const audioUrl = URL.createObjectURL(audioBlob);
            const audioPlayer = document.getElementById('audio-player');
            audioPlayer.src = audioUrl;
            
            // Convert to base64 for form submission
            const reader = new FileReader();
            reader.readAsDataURL(audioBlob);
            reader.onloadend = () => {
                document.getElementById('audio_data').value = reader.result;
            };
            
            // Show audio preview
            document.getElementById('audio-preview').classList.remove('d-none');
            
            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
        };
        
        mediaRecorder.start();
        recordingStartTime = Date.now();
        
        // Update UI
        document.getElementById('start-record-btn').classList.add('d-none');
        document.getElementById('stop-record-btn').classList.remove('d-none');
        document.getElementById('recording-timer').classList.remove('d-none');
        
        // Start timer
        timerInterval = setInterval(updateTimer, 1000);
        
        showToast('Kayıt başladı!', 'success');
    } catch (err) {
        showToast('Mikrofon erişimi reddedildi: ' + err.message, 'danger');
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        clearInterval(timerInterval);
        
        // Update UI
        document.getElementById('start-record-btn').classList.remove('d-none');
        document.getElementById('stop-record-btn').classList.add('d-none');
        document.getElementById('recording-timer').classList.add('d-none');
        
        showToast('Kayıt tamamlandı!', 'success');
    }
}

function updateTimer() {
    const elapsed = Date.now() - recordingStartTime;
    const minutes = Math.floor(elapsed / 60000);
    const seconds = Math.floor((elapsed % 60000) / 1000);
    document.getElementById('timer-display').textContent = 
        `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

function clearRecording() {
    if (confirm('Kaydı silmek istediğinizden emin misiniz?')) {
        audioChunks = [];
        document.getElementById('audio_data').value = '';
        document.getElementById('audio-preview').classList.add('d-none');
        document.getElementById('audio-player').src = '';
        showToast('Kayıt silindi', 'info');
    }
}

function processAudioToText() {
    const audioData = document.getElementById('audio_data').value;
    const contentTextarea = document.getElementById('content');
    
    if (!audioData) {
        showToast('Ses kaydı bulunamadı!', 'error');
        return;
    }
    
    // Loading durumu göster
    const processBtn = event.target;
    const originalHTML = processBtn.innerHTML;
    processBtn.disabled = true;
    processBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> İşleniyor...';
    
    // AJAX ile ses dosyasını metne çevir
    fetch('/reports/process-audio', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
        },
        body: JSON.stringify({ audio_data: audioData })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Mevcut içeriğe ekle veya üzerine yaz
            if (contentTextarea.value.trim()) {
                if (confirm('İçerik alanında zaten metin var. Ses metnini eklemek ister misiniz?')) {
                    contentTextarea.value += '\n\n' + data.text;
                } else {
                    contentTextarea.value = data.text;
                }
            } else {
                contentTextarea.value = data.text;
            }
            showToast('Ses başarıyla metne dönüştürüldü!', 'success');
            
            // Scroll to content area
            contentTextarea.scrollIntoView({ behavior: 'smooth', block: 'center' });
            contentTextarea.focus();
        } else {
            showToast(data.message || 'Ses işlenirken hata oluştu', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Ses işlenirken bir hata oluştu', 'error');
    })
    .finally(() => {
        processBtn.disabled = false;
        processBtn.innerHTML = originalHTML;
    });
}

// Export functions for use in other scripts
window.RaporcuWeb = {
    copyToClipboard,
    showToast,
    formatNumber,
    formatCurrency,
    setButtonLoading,
    fetchAPI,
    debounce,
    smoothScrollTo,
    isInViewport,
    storage
};
