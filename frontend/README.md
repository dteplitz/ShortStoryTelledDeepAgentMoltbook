# 🎨 Muse - Frontend PWA

Beautiful dark-themed Progressive Web App for the Muse story-telling agent.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Run Development Server

```bash
npm run dev
```

The app will open at `http://localhost:5173`

### 3. Build for Production

```bash
npm run build
npm run preview  # Preview production build
```

## ✨ Features

### 📱 Progressive Web App (PWA)
- ✅ **Installable** on mobile and desktop
- ✅ **Offline support** with Service Worker
- ✅ **App-like experience** with standalone mode
- ✅ **Custom icons** with gradient branding
- ✅ **Responsive design** optimized for all devices

### 🎯 Core Features
- **🌑 Dark Theme** - Elegant dark interface with purple/blue gradients
- **🎯 Hero Generate Button** - Large, centered story generation button
- **📚 Story Title Cards** - Browse stories as beautiful cards with excerpts
- **📖 Right Sidebar Reader** - Click any story to read it in a sliding sidebar
- **🧠 Editable Identity Panel** - Auto-save emotions, topics, and personality
- **📚 Memories Viewer** - View agent's memories (read-only)
- **⚡ Animated Progress** - Visual feedback during story generation

## 📱 Installing as PWA

### Desktop (Chrome/Edge/Brave):
1. Open the app in your browser
2. Look for the install icon (⊕) in the address bar
3. Click "Install"
4. The app will open in its own window!

### Mobile (Android):
1. Open in Chrome
2. Tap the menu (⋮)
3. Select "Add to Home Screen"
4. Tap "Add"

### Mobile (iOS/Safari):
1. Open in Safari
2. Tap the share button
3. Select "Add to Home Screen"
4. Tap "Add"

## 🎨 Design Features

### Layout
- **Header**: Compact with Muse branding and hidden identity toggle
- **Hero Section**: Large centered "Generate New Story" button
- **Story Grid**: Cards showing story titles, excerpts, and metadata
- **Right Sidebar**: Slides in to display full story content
- **Left Sidebar**: Hidden identity panel (toggle with 🧠 button)

### Color Palette
- Background: Deep navy (`#0a0e27`)
- Accents: Purple gradient (`#667eea` → `#a78bfa`)
- Text: Light gray (`#e0e0e0`, `#9ca3af`)
- Cards: Semi-transparent dark overlays

## 📁 Structure

```
frontend/
├── public/
│   ├── manifest.json          # PWA manifest
│   ├── sw.js                  # Service Worker
│   ├── icon-192.png          # PWA icon (192x192)
│   ├── icon-512.png          # PWA icon (512x512)
│   └── browserconfig.xml     # Windows tiles config
├── src/
│   ├── components/
│   │   ├── IdentityPanel.jsx      # Editable identity (left)
│   │   ├── StoryCards.jsx         # Grid of story title cards
│   │   ├── StoryReader.jsx        # Right sidebar for reading
│   │   ├── MemoriesViewer.jsx     # Memories modal viewer
│   │   └── GenerateButton.jsx     # Hero generate button
│   ├── App.jsx                     # Main app with layout
│   ├── main.jsx                    # Entry point + SW registration
│   └── index.css                   # Global dark theme styles
├── package.json
└── README.md
```

## 🎮 User Interactions

1. **Generate Story**: Click the big button → Watch animated progress
2. **Browse Stories**: Scroll through story cards below
3. **Read Story**: Click any card → Right sidebar slides in
4. **Close Reader**: Click X, click backdrop, or press Escape
5. **View Identity**: Click 🧠 icon → Left sidebar slides in
6. **Edit Identity**: 
   - Click ✏️ to edit any item
   - Press Enter to save (auto-saves to backend)
   - Click 🗑️ to delete items
   - Click "+ Add" to add new items
7. **View Memories**: Click "View 18 Memories" badge

## 🔌 Backend Integration

Currently uses **mock data**. To connect to backend:

### Required API Endpoints:
```
GET  /identity              - Fetch emotions, topics, personality
PUT  /identity/emotions     - Update emotions
PUT  /identity/topics       - Update topics  
PUT  /identity/personality  - Update personality
GET  /memories              - Fetch all memories
GET  /stories               - List all stories
GET  /stories/:filename     - Get specific story
POST /generate              - Trigger story generation
GET  /status                - Get generation status
```

### Integration Points:
- `IdentityPanel.jsx` - Replace `saveToBackend()` with real API calls
- `StoryCards.jsx` - Replace `mockStories` with API fetch
- `MemoriesViewer.jsx` - Replace `mockMemories` with API fetch
- `GenerateButton.jsx` - Connect to `/generate` endpoint

## 🛠️ Built With

- **React 18** - UI framework
- **Vite** - Build tool (faster than Create React App)
- **CSS3** - Custom styling with gradients and animations
- **PWA** - Service Worker + Manifest for installability

## 📊 PWA Audit

To check your PWA score:
1. Open Chrome DevTools (F12)
2. Go to "Lighthouse" tab
3. Select "Progressive Web App"
4. Click "Analyze page load"

Target: 90+ PWA score ✅

## 🚀 Deployment

### Option 1: Netlify
```bash
npm run build
# Drag and drop 'dist' folder to Netlify
```

### Option 2: Vercel
```bash
npm run build
vercel --prod
```

### Option 3: Static Host
```bash
npm run build
# Upload 'dist' folder to any static host
```

**Important**: Make sure HTTPS is enabled for PWA features to work!

---

**Note**: This is currently a visual MVP with mock data. Backend integration coming next! 🚀

## 📝 Next Steps

- [ ] Connect to FastAPI backend
- [ ] Implement real-time story generation updates
- [ ] Add push notifications for completed stories
- [ ] Add offline story reading
- [ ] Implement data sync when coming back online
