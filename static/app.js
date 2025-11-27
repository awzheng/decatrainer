/**
 * deca - DECA Flashcard Bank
 * Frontend application
 */

// Initialize markdown-it
const md = window.markdownit({
    html: true,
    linkify: true,
    typographer: true
});

// State
let currentPath = null;

// DOM Elements
const navTree = document.getElementById('nav-tree');
const welcome = document.getElementById('welcome');
const article = document.getElementById('article');
const articleBody = document.getElementById('article-body');
const breadcrumb = document.getElementById('breadcrumb');
const themeToggle = document.getElementById('theme-toggle');

// =========================
// Theme Management
// =========================

function initTheme() {
    const savedTheme = localStorage.getItem('deca-theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('deca-theme', next);
}

// =========================
// LaTeX Rendering
// =========================

function renderLatex(element) {
    if (typeof renderMathInElement === 'undefined') {
        setTimeout(() => renderLatex(element), 100);
        return;
    }
    
    renderMathInElement(element, {
        delimiters: [
            { left: '$$', right: '$$', display: true },
            { left: '$', right: '$', display: false },
            { left: '\\[', right: '\\]', display: true },
            { left: '\\(', right: '\\)', display: false }
        ],
        throwOnError: false,
        errorColor: '#E53935'
    });
}

// =========================
// Navigation Tree
// =========================

async function loadFileTree() {
    try {
        const response = await fetch('/tree');
        const tree = await response.json();
        
        if (tree.length === 0) {
            navTree.innerHTML = `
                <div class="nav-empty">
                    <p>No content yet.</p>
                    <p style="font-size: 0.85rem; margin-top: 0.5rem;">
                        Add <code>.md</code> files to the <code>content/</code> folder.
                    </p>
                </div>
            `;
            return;
        }
        
        navTree.innerHTML = renderTree(tree);
        addNavListeners();
    } catch (error) {
        console.error('Failed to load file tree:', error);
        navTree.innerHTML = '<div class="nav-error">Failed to load navigation</div>';
    }
}

function renderTree(items) {
    return items.map(item => {
        if (item.type === 'directory') {
            return `
                <div class="nav-folder">
                    <div class="nav-folder-header">
                        <span class="nav-folder-icon">▼</span>
                        ${item.name}
                    </div>
                    <div class="nav-folder-items">
                        ${renderTree(item.children)}
                    </div>
                </div>
            `;
        } else {
            return `
                <a class="nav-item" data-path="${item.path}">
                    ${item.name}
                </a>
            `;
        }
    }).join('');
}

function addNavListeners() {
    // Folder toggle
    document.querySelectorAll('.nav-folder-header').forEach(header => {
        header.addEventListener('click', () => {
            header.parentElement.classList.toggle('collapsed');
        });
    });
    
    // File click
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const path = item.dataset.path;
            loadContent(path);
            
            // Update active state
            document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
        });
    });
}

// =========================
// Content Loading
// =========================

async function loadContent(path) {
    try {
        const response = await fetch(`/content/${path}`);
        
        if (!response.ok) {
            throw new Error('Failed to load content');
        }
        
        const data = await response.json();
        currentPath = path;
        
        // Update breadcrumb
        const parts = path.split('/');
        breadcrumb.innerHTML = parts.map((part, i) => {
            const name = part.replace('.md', '').replace(/_/g, ' ');
            const isLast = i === parts.length - 1;
            return `<span>${name}</span>${isLast ? '' : ' / '}`;
        }).join('');
        
        // Render markdown
        articleBody.innerHTML = md.render(data.content);
        
        // Render LaTeX equations
        renderLatex(articleBody);
        
        // Show article, hide welcome
        welcome.hidden = true;
        article.hidden = false;
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
        
    } catch (error) {
        console.error('Failed to load content:', error);
        articleBody.innerHTML = `
            <div class="error-message">
                <h2>Failed to load content</h2>
                <p>Could not load the requested file.</p>
            </div>
        `;
    }
}

// =========================
// Event Listeners
// =========================

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    loadFileTree();
});

// Theme toggle
themeToggle.addEventListener('click', toggleTheme);

