// Firebase SDK'dan ihtiyacımız olan fonksiyonları import edin
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";
import { getFirestore, collection, addDoc, getDocs, doc, updateDoc, deleteDoc, setDoc, serverTimestamp, getDoc } from "https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js";

// Web uygulamanızın Firebase yapılandırması
const firebaseConfig = {
    apiKey: "AIzaSyCCYaPrtmnncISnto1u9zE2ioVbWfEccFQ",
    authDomain: "daily-routine-planner-6d905.firebaseapp.com",
    projectId: "daily-routine-planner-6d905",
    storageBucket: "daily-routine-planner-6d905.firebasestorage.app",
    messagingSenderId: "1015388255385",
    appId: "1:1015388255385:web:95434252725a997e8db408",
    measurementId: "G-YWX70BB782"
};

// Firebase'i başlat
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

console.log("Firebase initialized and connected!");

// --- GLOBAL DEĞİŞKENLER ---
let tasks = [];
let classes = [];
let currentUser = null;
let currentEditingTaskId = null; // Görev düzenleme modu için
let currentEditingClassId = null; // Ders düzenleme modu için
let clockInterval = null;
let notificationCheckInterval = null;
let pomodoroSettings = { pomodoro: 25, short: 5, long: 15 };
let notifiedEvents = JSON.parse(sessionStorage.getItem('notifiedEvents')) || {};

// --- DOM ELEMENTLERİ ---
const loginPage = document.getElementById('login-page');
const appContainer = document.getElementById('app-container');
const pageSections = document.querySelectorAll('.page-section');
const navItems = document.querySelectorAll('.nav-item, .logo');
const navMenu = document.getElementById('nav-menu');
const navToggle = document.getElementById('nav-toggle');
const loginForm = document.getElementById('loginForm');
const signUpForm = document.getElementById('signUpForm');
const toggleToSignUp = document.getElementById('toggleToSignUp');
const toggleToLogin = document.getElementById('toggleToLogin');
const authMessage = document.getElementById('auth-message');
const modals = document.querySelectorAll('.modal');
const addTaskModal = document.getElementById('addTaskModal');
const addClassModal = document.getElementById('addClassModal');
const allTasksList = document.getElementById('all-tasks-list');
const dashboardTaskList = document.getElementById('dashboard-task-list');
const scheduleContainer = document.getElementById('schedule-grid-container');

// --- VERİ YÜKLEME ---
const loadUserData = async (userUid) => {
    // Firestore'dan verileri çek
    const tasksCol = collection(db, `users/${userUid}/tasks`);
    const taskSnapshot = await getDocs(tasksCol);
    tasks = taskSnapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));

    const classesCol = collection(db, `users/${userUid}/classes`);
    const classSnapshot = await getDocs(classesCol);
    classes = classSnapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));

    const settingsDocRef = doc(db, `users/${userUid}/settings/pomodoro`);
    const settingsDoc = await getDoc(settingsDocRef);
    if (settingsDoc.exists()) {
        pomodoroSettings = settingsDoc.data();
    } else {
        pomodoroSettings = { pomodoro: 25, short: 5, long: 15 };
        await setDoc(settingsDocRef, pomodoroSettings);
    }
};

// --- AUTH VE SAYFA YÖNETİMİ ---
const showLoginPage = () => {
    appContainer.style.display = 'none';
    loginPage.style.display = 'flex';
    loginPage.classList.add('active');
};

const showApp = async (userObject) => {
    currentUser = userObject;
    await loadUserData(currentUser.uid);
    loginPage.style.display = 'none';
    loginPage.classList.remove('active');
    appContainer.style.display = 'block';
    document.getElementById('welcome-message').textContent = `Hoş Geldin, ${currentUser.username}! 🌟`;
    
    if (clockInterval) clearInterval(clockInterval);
    updateClock();
    clockInterval = setInterval(updateClock, 1000);

    if (notificationCheckInterval) clearInterval(notificationCheckInterval);
    notificationCheckInterval = setInterval(checkUpcomingEvents, 60000); 

    initializeAppData();
};

onAuthStateChanged(auth, async (user) => {
    if (user) {
        const userDoc = await getDoc(doc(db, "users", user.uid));
        const username = userDoc.exists() ? userDoc.data().username : user.email.split('@')[0];
        const userWithUsername = { ...user, username: username };
        showApp(userWithUsername);
    } else {
        sessionStorage.removeItem('notifiedEvents');
        notifiedEvents = {};
        currentUser = null;
        tasks = [];
        classes = [];
        if (clockInterval) clearInterval(clockInterval);
        if (notificationCheckInterval) clearInterval(notificationCheckInterval);
        showLoginPage();
    }
});

toggleToSignUp.addEventListener('click', () => {
    loginForm.style.display = 'none';
    signUpForm.style.display = 'block';
    toggleToSignUp.style.display = 'none';
    toggleToLogin.style.display = 'block';
    authMessage.textContent = '';
});

toggleToLogin.addEventListener('click', () => {
    signUpForm.style.display = 'none';
    loginForm.style.display = 'block';
    toggleToLogin.style.display = 'none';
    toggleToSignUp.style.display = 'block';
    authMessage.textContent = '';
});

signUpForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('signUpUsername').value.trim();
    const email = document.getElementById('signUpEmail').value.trim();
    const password = document.getElementById('signUpPassword').value;

    try {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        await setDoc(doc(db, "users", userCredential.user.uid), {
            username: username,
            email: email,
            createdAt: serverTimestamp()
        });
        authMessage.textContent = 'Hesap başarıyla oluşturuldu! Lütfen giriş yapın.';
        authMessage.className = 'auth-success';
        signUpForm.reset();
        toggleToLogin.click();
    } catch (error) {
        let errorMessage = 'Kayıt sırasında bir hata oluştu.';
        if (error.code === 'auth/email-already-in-use') errorMessage = 'Bu e-posta adresi zaten kullanımda.';
        else if (error.code === 'auth/weak-password') errorMessage = 'Şifre en az 6 karakter olmalıdır.';
        authMessage.textContent = errorMessage;
        authMessage.className = 'auth-error';
    }
});

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;
    try {
        await signInWithEmailAndPassword(auth, email, password);
    } catch (error) {
        let errorMessage = 'Giriş sırasında bir hata oluştu.';
        if (error.code === 'auth/user-not-found' || error.code === 'auth/wrong-password' || error.code === 'auth/invalid-credential') {
            errorMessage = 'Geçersiz e-posta veya şifre.';
        }
        authMessage.textContent = errorMessage;
        authMessage.className = 'auth-error';
    }
});

document.getElementById('logout-btn').addEventListener('click', async (e) => {
    e.preventDefault();
    await signOut(auth);
});

// --- MODAL YÖNETİMİ ---
const showModal = (modalId) => document.getElementById(modalId)?.classList.add('active');

const closeModal = () => {
    modals.forEach(modal => modal.classList.remove('active'));
    // Görev modalını sıfırla
    currentEditingTaskId = null;
    addTaskModal.querySelector('h3').textContent = 'Yeni Görev Ekle';
    addTaskModal.querySelector('button[type="submit"]').innerHTML = '<i class="fas fa-save"></i> Görevi Kaydet';
    document.getElementById('addTaskForm').reset();
    
    // Ders modalını sıfırla
    currentEditingClassId = null;
    addClassModal.querySelector('h3').textContent = 'Yeni Ders Ekle';
    addClassModal.querySelector('button[type="submit"]').innerHTML = '<i class="fas fa-save"></i> Dersi Kaydet';
    document.getElementById('addClassForm').reset();
};

document.querySelectorAll('[id^="open-"], #dashboard-add-task-btn').forEach(btn => {
    const modalId = btn.id.includes('addTask') || btn.id.includes('dashboard-add') ? 'addTaskModal' : 'addClassModal';
    btn.addEventListener('click', () => showModal(modalId));
});

document.getElementById('pomodoro-settings-btn').addEventListener('click', () => {
    document.getElementById('settingPomodoro').value = pomodoroSettings.pomodoro;
    document.getElementById('settingShortBreak').value = pomodoroSettings.short;
    document.getElementById('settingLongBreak').value = pomodoroSettings.long;
    showModal('pomodoroSettingsModal');
});

modals.forEach(modal => {
    modal.addEventListener('click', (e) => {
        if (e.target === modal || e.target.closest('.modal-close-btn')) {
            closeModal();
        }
    });
});

// --- GÖREV YÖNETİMİ (EKLEME/SİLME/DÜZENLEME) ---
const renderTasks = () => {
    allTasksList.innerHTML = '';
    dashboardTaskList.innerHTML = '';
    const sortedTasks = [...tasks].sort((a, b) => (a.completed - b.completed) || a.time.localeCompare(b.time));
    if (sortedTasks.length === 0) {
        const emptyMsg = '<p style="text-align:center; opacity: 0.7;">Henüz görev eklenmemiş.</p>';
        allTasksList.innerHTML = emptyMsg;
        dashboardTaskList.innerHTML = emptyMsg;
    } else {
        sortedTasks.forEach(task => {
            const taskHTML = `
                <div class="task-item ${task.completed ? 'completed' : ''}" data-id="${task.id}">
                    <div class="task-checkbox ${task.completed ? 'completed' : ''}" role="button">${task.completed ? '<i class="fas fa-check"></i>' : ''}</div>
                    <div class="task-content"><div class="task-title">${task.title}</div></div>
                    <div class="task-time">${task.time}</div>
                    <div class="task-actions">
                        <button class="task-edit-btn" title="Görevi Düzenle"><i class="fas fa-edit"></i></button>
                        <button class="task-delete-btn" title="Görevi Sil"><i class="fas fa-trash-alt"></i></button>
                    </div>
                </div>`;
            allTasksList.innerHTML += taskHTML;
            dashboardTaskList.innerHTML += taskHTML; // Sadece bugün olanları göstermek için bir filtre eklenebilir. Şimdilik hepsi.
        });
    }
    updateStats();
};

document.getElementById('addTaskForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!currentUser) return;
    const form = e.target;
    const taskData = {
        title: form.taskTitle.value,
        meta: form.taskMeta.value,
        time: form.taskTime.value,
    };

    if (currentEditingTaskId) {
        // Güncelleme modu
        const taskRef = doc(db, `users/${currentUser.uid}/tasks`, currentEditingTaskId);
        await updateDoc(taskRef, taskData);
    } else {
        // Ekleme modu
        taskData.completed = false;
        taskData.createdAt = serverTimestamp();
        await addDoc(collection(db, `users/${currentUser.uid}/tasks`), taskData);
    }
    await loadUserData(currentUser.uid);
    renderTasks();
    closeModal();
});

async function handleTaskInteraction(e) {
    const taskItem = e.target.closest('.task-item');
    if (!taskItem || !currentUser) return;
    const taskId = taskItem.dataset.id;
    
    if (e.target.closest('.task-edit-btn')) {
        const taskToEdit = tasks.find(t => t.id === taskId);
        if (taskToEdit) {
            currentEditingTaskId = taskId;
            addTaskModal.querySelector('h3').textContent = 'Görevi Düzenle';
            addTaskModal.querySelector('button[type="submit"]').innerHTML = '<i class="fas fa-save"></i> Değişiklikleri Kaydet';
            document.getElementById('taskTitle').value = taskToEdit.title;
            document.getElementById('taskMeta').value = taskToEdit.meta;
            document.getElementById('taskTime').value = taskToEdit.time;
            showModal('addTaskModal');
        }
    } else if (e.target.closest('.task-checkbox')) {
        const taskRef = doc(db, `users/${currentUser.uid}/tasks`, taskId);
        const currentTask = tasks.find(t => t.id === taskId);
        await updateDoc(taskRef, { completed: !currentTask.completed });
        await loadUserData(currentUser.uid);
        renderTasks();
    } else if (e.target.closest('.task-delete-btn')) {
        const taskRef = doc(db, `users/${currentUser.uid}/tasks`, taskId);
        await deleteDoc(taskRef);
        await loadUserData(currentUser.uid);
        renderTasks();
    }
}
allTasksList.addEventListener('click', handleTaskInteraction);
dashboardTaskList.addEventListener('click', handleTaskInteraction);

// --- DERS PROGRAMI YÖNETİMİ (EKLEME/SİLME/DÜZENLEME) ---
const daysOfWeek = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"];

const renderClasses = () => {
    scheduleContainer.innerHTML = '';
    daysOfWeek.forEach((day) => {
        const dayClasses = classes.filter(c => c.day === day).sort((a,b) => a.start.localeCompare(b.start));
        const classesHTML = dayClasses.map(c => `
            <div class="class-item" data-id="${c.id}">
                <strong>${c.name}</strong><br>${c.start} - ${c.end}<br><small>${c.teacher || ''}</small>
                <button class="class-edit-btn" title="Dersi Düzenle"><i class="fas fa-edit"></i></button>
                <button class="class-delete-btn" title="Dersi Sil"><i class="fas fa-times"></i></button>
            </div>`).join('');
        scheduleContainer.innerHTML += `<div class="day-column"><div class="day-header">${day}</div>${classesHTML || '<p style="text-align:center; font-size: 0.9em; opacity: 0.6; margin-top:1rem;">Ders yok</p>'}</div>`;
    });
    updateStats();
};

document.getElementById('addClassForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!currentUser) return;
    const form = e.target;
    const classData = {
        name: form.className.value,
        day: form.classDay.value,
        start: form.classTimeStart.value,
        end: form.classTimeEnd.value,
        teacher: form.classTeacher.value,
    };
    
    if (currentEditingClassId) {
        // Güncelleme modu
        const classRef = doc(db, `users/${currentUser.uid}/classes`, currentEditingClassId);
        await updateDoc(classRef, classData);
    } else {
        // Ekleme modu
        classData.createdAt = serverTimestamp();
        await addDoc(collection(db, `users/${currentUser.uid}/classes`), classData);
    }
    await loadUserData(currentUser.uid);
    renderClasses();
    closeModal();
});

scheduleContainer.addEventListener('click', async (e) => {
    if (!currentUser) return;
    const classItem = e.target.closest('.class-item');
    if (!classItem) return;
    const classId = classItem.dataset.id;
    
    if (e.target.closest('.class-edit-btn')) {
        const classToEdit = classes.find(c => c.id === classId);
        if (classToEdit) {
            currentEditingClassId = classId;
            addClassModal.querySelector('h3').textContent = 'Dersi Düzenle';
            addClassModal.querySelector('button[type="submit"]').innerHTML = '<i class="fas fa-save"></i> Değişiklikleri Kaydet';
            document.getElementById('className').value = classToEdit.name;
            document.getElementById('classDay').value = classToEdit.day;
            document.getElementById('classTimeStart').value = classToEdit.start;
            document.getElementById('classTimeEnd').value = classToEdit.end;
            document.getElementById('classTeacher').value = classToEdit.teacher;
            showModal('addClassModal');
        }
    } else if (e.target.closest('.class-delete-btn')) {
        await deleteDoc(doc(db, `users/${currentUser.uid}/classes`, classId));
        await loadUserData(currentUser.uid);
        renderClasses();
    }
});

// --- DİĞER FONKSİYONLAR (STATS, POMODORO, NAV, CLOCK VB.) ---
const updateStats = () => {
    const totalTasks = tasks.length;
    const completedTasks = tasks.filter(t => t.completed).length;
    const progress = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;
    document.getElementById('stats-total-tasks').textContent = totalTasks;
    document.getElementById('stats-completed-tasks').textContent = completedTasks;
    document.getElementById('stats-pending-tasks').textContent = totalTasks - completedTasks;
    document.getElementById('stats-total-classes').textContent = classes.length;
    document.getElementById('progress-fill').style.width = `${progress}%`;
    document.getElementById('progress-text').textContent = totalTasks > 0 ? `${progress}% tamamlandı - Harika gidiyorsun! 🚀` : `Başlamak için bir görev ekle!`;
};

const showPage = (pageId) => {
    pageSections.forEach(section => { if(section.id !== 'login-page') section.classList.remove('active'); });
    document.getElementById(pageId)?.classList.add('active');
    navItems.forEach(item => item.classList.remove('active'));
    document.querySelector(`.nav-item[data-page="${pageId}"], .logo[data-page="${pageId}"]`)?.classList.add('active');
    navMenu.classList.remove('active');
};

navItems.forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const pageId = item.getAttribute('data-page');
        if (pageId) showPage(pageId);
    });
});

navToggle.addEventListener('click', () => navMenu.classList.toggle('active'));

const pomodoroDisplay = document.getElementById('pomodoro-display');
let timer, isRunning = false, timeLeft;
let currentMode = 'pomodoro';
const alarmSound = new Audio('https://www.soundjay.com/buttons/sounds/button-16.mp3');

const updateDisplay = () => { let m = Math.floor(timeLeft / 60), s = timeLeft % 60; pomodoroDisplay.textContent = `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`; document.title = `${pomodoroDisplay.textContent} - StudyFlow`; };
const startTimer = () => { if (isRunning) return; isRunning = true; timer = setInterval(() => { timeLeft--; updateDisplay(); if (timeLeft <= 0) { clearInterval(timer); isRunning = false; alarmSound.play(); alert("Süre doldu!"); resetTimer(); } }, 1000); };
const pauseTimer = () => { clearInterval(timer); isRunning = false; };
const resetTimer = () => { pauseTimer(); timeLeft = (pomodoroSettings[currentMode] || 25) * 60; updateDisplay(); };
const setMode = (mode) => { currentMode = mode; resetTimer(); };

document.getElementById('pomodoro-start').addEventListener('click', startTimer);
document.getElementById('pomodoro-pause').addEventListener('click', pauseTimer);
document.getElementById('pomodoro-reset').addEventListener('click', resetTimer);
document.getElementById('mode-pomodoro').addEventListener('click', () => setMode('pomodoro'));
document.getElementById('mode-short').addEventListener('click', () => setMode('short'));
document.getElementById('mode-long').addEventListener('click', () => setMode('long'));

document.getElementById('pomodoroSettingsForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    pomodoroSettings.pomodoro = parseInt(document.getElementById('settingPomodoro').value, 10);
    pomodoroSettings.short = parseInt(document.getElementById('settingShortBreak').value, 10);
    pomodoroSettings.long = parseInt(document.getElementById('settingLongBreak').value, 10);
    if (currentUser) {
        const settingsDocRef = doc(db, `users/${currentUser.uid}/settings/pomodoro`);
        await setDoc(settingsDocRef, pomodoroSettings);
    }
    resetTimer();
    closeModal();
});

function updateClock() {
    const clockElement = document.getElementById('live-clock');
    if (!clockElement) return;
    const now = new Date();
    const days = ["Pazar", "Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi"];
    const months = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"];
    const dayName = days[now.getDay()];
    const day = now.getDate();
    const monthName = months[now.getMonth()];
    const year = now.getFullYear();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    const seconds = now.getSeconds().toString().padStart(2, '0');
    clockElement.innerHTML = `<span>${hours}:${minutes}:${seconds}</span><span style="opacity: 0.8; margin-left: 10px;">${day} ${monthName} ${year}, ${dayName}</span>`;
}

// BİLDİRİM FONKSİYONLARI (send-mail.js'e bağlı olduğu için şimdilik pasif)
const checkUpcomingEvents = () => { /* İsteğe bağlı olarak eklenebilir */ };
const showNotification = (event) => { /* İsteğe bağlı olarak eklenebilir */ };


// --- UYGULAMA BAŞLATMA ---
const initializeAppData = () => {
    renderTasks();
    renderClasses();
    setMode('pomodoro');
    showPage('dashboard');
    checkUpcomingEvents();
};
