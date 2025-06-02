class HireIntelDashboard {
    constructor() {
        this.currentPage = 'dashboard';
        this.candidates = [];
        this.jobs = [];
        this.interviews = [];
        this.eventSource = null;

        this.init();
    }

    init() {
        this.setupNavigation();
        this.setupEventListeners();
        this.loadInitialData();
        this.startRealTimeUpdates();
    }

    setupNavigation() {
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.addEventListener('click', () => {
                const page = item.dataset.page;
                this.switchPage(page);
            });
        });
    }

    switchPage(page) {
        // Hide all pages
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

        // Show selected page
        document.getElementById(`${page}-page`).classList.add('active');
        document.querySelector(`[data-page="${page}"]`).classList.add('active');

        this.currentPage = page;

        // Load page-specific data
        switch(page) {
            case 'dashboard':
                this.loadDashboardData();
                break;
            case 'jobs':
                this.loadJobsData();
                break;
            case 'candidates':
                this.loadCandidatesData();
                break;
            case 'interviews':
                this.loadInterviewsData();
                break;
            case 'pipeline':
                this.loadPipelineData();
                break;
            case 'analytics':
                this.loadAnalyticsData();
                break;
        }
    }

    setupEventListeners() {
        // Job form submission
        document.getElementById('job-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createJob(new FormData(e.target));
        });

        // Schedule form submission
        document.getElementById('schedule-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.scheduleInterviews(new FormData(e.target));
        });

        // Status filter
        const statusFilter = document.getElementById('status-filter');
        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.filterCandidates(e.target.value);
            });
        }

        // Search functionality
        const searchInput = document.querySelector('.search-bar input');
        searchInput.addEventListener('input', (e) => {
            this.performSearch(e.target.value);
        });
    }

    async loadInitialData() {
        try {
            await Promise.all([
                this.fetchJobs(),
                this.fetchCandidates(),
                this.fetchInterviews()
            ]);
            this.updateDashboardStats();
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showNotification('Error loading data', 'error');
        }
    }

    async fetchJobs() {
        try {
            const response = await fetch('/api/v1/admin/jobs');
            const data = await response.json();
            this.jobs = data.data || [];
            return this.jobs;
        } catch (error) {
            console.error('Error fetching jobs:', error);
            return [];
        }
    }

    async fetchCandidates() {
        try {
            const response = await fetch('/api/v1/admin/candidates/stream');
            // For now, we'll use a simple fetch. The stream will be handled separately
            this.candidates = []; // Will be populated by the real-time stream
            return this.candidates;
        } catch (error) {
            console.error('Error fetching candidates:', error);
            return [];
        }
    }

    async fetchInterviews() {
        try {
            const response = await fetch('/api/v1/admin/interviews/schedules');
            const data = await response.json();
            this.interviews = data.data || [];
            return this.interviews;
        } catch (error) {
            console.error('Error fetching interviews:', error);
            return [];
        }
    }

    startRealTimeUpdates() {
        if (this.eventSource) {
            this.eventSource.close();
        }

        this.eventSource = new EventSource('/api/v1/admin/candidates/stream');

        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (!data.error) {
                    this.candidates = data.data.candidates;
                    this.updateCandidatesDisplay();
                    this.updatePipelineStatus();
                }
            } catch (error) {
                console.error('Error parsing SSE data:', error);
            }
        };

        this.eventSource.onerror = (error) => {
            console.error('SSE error:', error);
            this.showNotification('Connection lost. Attempting to reconnect...', 'warning');
        };
    }

    updateDashboardStats() {
        document.getElementById('active-jobs').textContent = 
            this.jobs.filter(job => job.status === 'active').length;

        document.getElementById('total-candidates').textContent = this.candidates.length;

        document.getElementById('scheduled-interviews').textContent = 
            this.interviews.filter(interview => interview.status === 'scheduled').length;

        document.getElementById('hired-candidates').textContent = 
            this.candidates.filter(candidate => candidate.status === 'hired').length;
    }

    loadDashboardData() {
        this.updateDashboardStats();
        this.loadRecentActivity();
        this.loadPipelineChart();
    }

    loadRecentActivity() {
        const activityList = document.getElementById('recent-activity-list');
        const activities = [
            { text: 'New candidate applied for Senior Developer', time: '2 minutes ago', type: 'application' },
            { text: 'Interview scheduled with Jane Smith', time: '15 minutes ago', type: 'interview' },
            { text: 'John Doe moved to final round', time: '1 hour ago', type: 'progress' },
            { text: 'New job posted: Frontend Engineer', time: '2 hours ago', type: 'job' }
        ];

        activityList.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <div class="activity-text">${activity.text}</div>
                <div class="activity-time">${activity.time}</div>
            </div>
        `).join('');
    }

    loadPipelineChart() {
        // Simple pipeline visualization
        const chartContainer = document.getElementById('pipeline-chart');
        const stages = [
            { name: 'Applied', count: this.candidates.filter(c => c.status === 'applied').length },
            { name: 'Screening', count: this.candidates.filter(c => c.pipeline_status?.includes('extract')).length },
            { name: 'Interview', count: this.candidates.filter(c => c.status === 'interviewing').length },
            { name: 'Hired', count: this.candidates.filter(c => c.status === 'hired').length }
        ];

        chartContainer.innerHTML = stages.map(stage => `
            <div class="pipeline-stage">
                <div class="stage-name">${stage.name}</div>
                <div class="stage-count">${stage.count}</div>
            </div>
        `).join('');
    }

    loadJobsData() {
        const tbody = document.getElementById('jobs-tbody');
        tbody.innerHTML = this.jobs.map(job => `
            <tr>
                <td>${job.title}</td>
                <td>${job.industry || 'Technology'}</td>
                <td>${job.location}</td>
                <td><span class="status-badge status-${job.status}">${job.status}</span></td>
                <td>${this.candidates.filter(c => c.job_id === job.id).length}</td>
                <td>${new Date(job.created_at).toLocaleDateString()}</td>
                <td>
                    <button class="btn btn-sm" onclick="editJob('${job.id}')">Edit</button>
                    <button class="btn btn-sm" onclick="deleteJob('${job.id}')">Delete</button>
                </td>
            </tr>
        `).join('');
    }

    loadCandidatesData() {
        this.updateCandidatesDisplay();
    }

    updateCandidatesDisplay() {
        const grid = document.getElementById('candidates-grid');
        if (!grid) return;

        grid.innerHTML = this.candidates.map(candidate => `
            <div class="candidate-card">
                <div class="candidate-header">
                    <div class="candidate-avatar">
                        ${candidate.first_name?.[0]}${candidate.last_name?.[0]}
                    </div>
                    <div class="candidate-info">
                        <h4>${candidate.first_name} ${candidate.last_name}</h4>
                        <p>${candidate.current_position || 'Position not specified'}</p>
                    </div>
                </div>
                <div class="candidate-details">
                    <p><strong>Email:</strong> ${candidate.email}</p>
                    <p><strong>Experience:</strong> ${candidate.years_of_experience || 'N/A'} years</p>
                    <p><strong>Status:</strong> <span class="status-badge status-${candidate.status}">${candidate.status}</span></p>
                    <p><strong>Pipeline:</strong> <span class="status-badge">${candidate.pipeline_status}</span></p>
                </div>
                <div class="candidate-actions">
                    <button class="btn btn-sm btn-primary" onclick="viewCandidate('${candidate.id}')">View Profile</button>
                    <button class="btn btn-sm btn-secondary" onclick="scheduleInterview('${candidate.id}')">Schedule</button>
                </div>
            </div>
        `).join('');
    }

    loadInterviewsData() {
        // Simple calendar view
        const calendar = document.getElementById('interview-calendar');
        calendar.innerHTML = `
            <div class="calendar-header">
                <h3>Upcoming Interviews</h3>
            </div>
            <div class="interview-list">
                ${this.interviews.map(interview => `
                    <div class="interview-item">
                        <div class="interview-time">${new Date(interview.scheduled_date).toLocaleString()}</div>
                        <div class="interview-candidate">${interview.candidate_name}</div>
                        <div class="interview-status">
                            <span class="status-badge status-${interview.status}">${interview.status}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    loadPipelineData() {
        this.updatePipelineStatus();
        this.loadPipelineFeed();
    }

    updatePipelineStatus() {
        const statusCounts = {
            xml: this.candidates.filter(c => c.pipeline_status === 'xml').length,
            extract: this.candidates.filter(c => c.pipeline_status?.includes('extract')).length,
            scraping: this.candidates.filter(c => c.pipeline_status?.includes('scrape')).length,
            profile: this.candidates.filter(c => c.pipeline_status?.includes('profile')).length
        };

        Object.keys(statusCounts).forEach(stage => {
            const countEl = document.getElementById(`${stage}-count`);
            const progressEl = document.getElementById(`${stage}-progress`);

            if (countEl) countEl.textContent = statusCounts[stage];
            if (progressEl) {
                const percentage = Math.min((statusCounts[stage] / Math.max(this.candidates.length, 1)) * 100, 100);
                progressEl.style.width = `${percentage}%`;
            }
        });
    }

    loadPipelineFeed() {
        const feedContent = document.getElementById('feed-content');
        if (!feedContent) return;

        // Simulate real-time feed updates
        const updates = this.candidates.slice(-10).map(candidate => ({
            text: `${candidate.first_name} ${candidate.last_name} - ${candidate.pipeline_status}`,
            time: new Date().toLocaleTimeString()
        }));

        feedContent.innerHTML = updates.map(update => `
            <div class="feed-item">
                <span>${update.text}</span>
                <small>${update.time}</small>
            </div>
        `).join('');

        // Auto-scroll to bottom
        feedContent.scrollTop = feedContent.scrollHeight;
    }

    loadAnalyticsData() {
        // Initialize charts using Chart.js
        this.initializeCharts();
    }

    initializeCharts() {
        // Hiring Funnel Chart
        const funnelCtx = document.getElementById('funnel-chart');
        if (funnelCtx) {
            new Chart(funnelCtx, {
                type: 'bar',
                data: {
                    labels: ['Applied', 'Screening', 'Interview', 'Offer', 'Hired'],
                    datasets: [{
                        data: [100, 75, 40, 20, 15],
                        backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#43e97b']
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } }
                }
            });
        }

        // Time to Hire Chart
        const timeCtx = document.getElementById('time-chart');
        if (timeCtx) {
            new Chart(timeCtx, {
                type: 'line',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [{
                        label: 'Days to Hire',
                        data: [25, 22, 28, 20, 18, 24],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        fill: true
                    }]
                },
                options: { responsive: true }
            });
        }
    }

    async createJob(formData) {
        try {
            const jobData = Object.fromEntries(formData);

            const response = await fetch('/api/v1/admin/jobs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(jobData)
            });

            const result = await response.json();

            if (!result.error) {
                this.jobs.push(result.data);
                this.showNotification('Job created successfully!', 'success');
                closeModal('job-modal');
                if (this.currentPage === 'jobs') {
                    this.loadJobsData();
                }
            } else {
                this.showNotification('Error creating job', 'error');
            }
        } catch (error) {
            console.error('Error creating job:', error);
            this.showNotification('Error creating job', 'error');
        }
    }

    async scheduleInterviews(formData) {
        try {
            const scheduleData = Object.fromEntries(formData);

            // Get selected candidates
            const selectedCandidates = Array.from(
                document.querySelectorAll('#candidate-selection input:checked')
            ).map(input => input.value);

            const requestData = {
                candidates: selectedCandidates,
                start_date: scheduleData.start_date,
                end_date: scheduleData.end_date
            };

            const response = await fetch('/api/v1/admin/interviews/schedule', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });

            const result = await response.json();

            if (!result.error) {
                this.showNotification('Interviews scheduled successfully!', 'success');
                closeModal('schedule-modal');
                if (this.currentPage === 'interviews') {
                    this.loadInterviewsData();
                }
            } else {
                this.showNotification('Error scheduling interviews', 'error');
            }
        } catch (error) {
            console.error('Error scheduling interviews:', error);
            this.showNotification('Error scheduling interviews', 'error');
        }
    }

    filterCandidates(status) {
        const filteredCandidates = status ? 
            this.candidates.filter(c => c.status === status) : 
            this.candidates;

        // Update display with filtered candidates
        const grid = document.getElementById('candidates-grid');
        if (grid) {
            // Use the filtered candidates for display
            const tempCandidates = this.candidates;
            this.candidates = filteredCandidates;
            this.updateCandidatesDisplay();
            this.candidates = tempCandidates;
        }
    }

    performSearch(query) {
        if (!query) return;

        const results = [
            ...this.candidates.filter(c => 
                c.first_name?.toLowerCase().includes(query.toLowerCase()) ||
                c.last_name?.toLowerCase().includes(query.toLowerCase()) ||
                c.email?.toLowerCase().includes(query.toLowerCase())
            ),
            ...this.jobs.filter(j => 
                j.title?.toLowerCase().includes(query.toLowerCase()) ||
                j.description?.toLowerCase().includes(query.toLowerCase())
            )
        ];

        console.log('Search results:', results);
        // Implement search results display
    }

    async makeRequest(url, options = {}) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            this.showNotification('API request failed. Please check your connection.', 'error');
            return null;
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element if it doesn't exist
        let notification = document.getElementById('notification');
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'notification';
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 15px;
                border-radius: 5px;
                color: white;
                z-index: 1000;
                font-weight: bold;
                max-width: 300px;
            `;
            document.body.appendChild(notification);
        }

        // Set notification style based on type
        const colors = {
            'error': '#dc3545',
            'success': '#28a745',
            'warning': '#ffc107',
            'info': '#17a2b8'
        };

        notification.style.backgroundColor = colors[type] || colors.info;
        notification.textContent = message;
        notification.style.display = 'block';

        // Auto hide after 3 seconds
        setTimeout(() => {
            notification.style.display = 'none';
        }, 3000);
    }
}

// Modal functions
function openJobModal() {
    document.getElementById('job-modal').style.display = 'block';
}

function openScheduleModal() {
    // Load available candidates for selection
    const selectionDiv = document.getElementById('candidate-selection');
    const dashboard = window.dashboard;

    if (dashboard && dashboard.candidates) {
        selectionDiv.innerHTML = dashboard.candidates
            .filter(c => c.status === 'applied' || c.status === 'interviewing')
            .map(candidate => `
                <label class="candidate-checkbox">
                    <input type="checkbox" value="${candidate.id}">
                    ${candidate.first_name} ${candidate.last_name} (${candidate.current_position || 'No position'})
                </label>
            `).join('');
    }

    document.getElementById('schedule-modal').style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function refreshPipeline() {
    window.dashboard?.loadPipelineData();
    window.dashboard?.showNotification('Pipeline data refreshed', 'success');
}

// Global functions for button actions
function editJob(jobId) {
    console.log('Edit job:', jobId);
    // Implement edit functionality
}

function deleteJob(jobId) {
    if (confirm('Are you sure you want to delete this job?')) {
        console.log('Delete job:', jobId);
        // Implement delete functionality
    }
}

function viewCandidate(candidateId) {
    console.log('View candidate:', candidateId);
    // Implement candidate detail view
}

function scheduleInterview(candidateId) {
    console.log('Schedule interview for:', candidateId);
    openScheduleModal();
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new HireIntelDashboard();
});

// Close modals when clicking outside
window.addEventListener('click', (event) => {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
});