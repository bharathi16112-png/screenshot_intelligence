import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Upload, Search, Brain, Zap, Cpu, Tag, ChevronRight, X,
  Loader2, Sparkles, Eye, Clock, ImageIcon, Layers
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = 'http://127.0.0.1:8010';

function App() {
  const [query, setQuery] = useState('');
  const [memories, setMemories] = useState([]);
  const [results, setResults] = useState([]);
  const [confidenceMessage, setConfidenceMessage] = useState('');
  const [topScore, setTopScore] = useState(0);
  const [aiAnswer, setAiAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedMemory, setSelectedMemory] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  useEffect(() => {
    fetchMemories();
  }, []);

  const fetchMemories = async () => {
    try {
      const res = await axios.get(`${API_BASE}/memories`);
      setMemories(res.data);
    } catch (err) {
      console.error("Failed to fetch memories", err);
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsUploading(true);
    setUploadSuccess(false);
    const formData = new FormData();
    formData.append('file', file);

    try {
      await axios.post(`${API_BASE}/upload`, formData);
      setUploadSuccess(true);
      fetchMemories();
      setTimeout(() => setUploadSuccess(false), 3000);
    } catch (err) {
      console.error("Upload failed", err);
    } finally {
      setIsUploading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setSearching(true);
    setAiAnswer('');
    try {
    const res = await axios.get(`${API_BASE}/search?q=${encodeURIComponent(query)}`);
      setResults(res.data.results);
      setAiAnswer(res.data.answer);
      setConfidenceMessage(res.data.confidence_message);
      setTopScore(res.data.top_score);
    } catch (err) {
      console.error("Search failed", err);
    } finally {
      setSearching(false);
    }
  };

  const getMatchClass = (similarity) => {
    if (!similarity) return '';
    if (similarity >= 0.7) return 'match-high';
    if (similarity >= 0.4) return 'match-medium';
    return 'match-low';
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Just now';
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
      });
    } catch {
      return 'Recent';
    }
  };

  const displayedMemories = results.length > 0 ? results : memories;

  return (
    <>
      {/* Animated Background */}
      <div className="scene-bg" />
      <div className="scene-grid" />

      <div className="app-shell">
        {/* ──── Header ──── */}
        <motion.header
          className="app-header"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="brand">
            <div className="brand-icon">
              <Brain size={22} color="white" />
            </div>
            <div>
              <div className="brand-title">Visual Memory AI</div>
              <div className="brand-sub">Multimodal Intelligence Engine</div>
            </div>
          </div>

          <div className="header-actions">
            <div className="stat-chip">
              <span className="dot" />
              <span>{memories.length} memories</span>
            </div>
            <label className="btn-upload" style={{ cursor: isUploading ? 'not-allowed' : 'pointer' }}>
              {isUploading ? (
                <Loader2 size={16} className="animate-spin" />
              ) : uploadSuccess ? (
                <Sparkles size={16} />
              ) : (
                <Upload size={16} />
              )}
              <span>{isUploading ? 'Processing...' : uploadSuccess ? 'Memorized!' : 'Add Memory'}</span>
              <input type="file" accept="image/*" style={{ display: 'none' }} onChange={handleUpload} disabled={isUploading} />
            </label>
          </div>
        </motion.header>

        {/* ──── Hero Search ──── */}
        <motion.section
          className="hero-search"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          <h1 className="hero-title">
            Search <span className="gradient-text">What You Saw</span>
          </h1>
          <p className="hero-subtitle">
            Upload screenshots and photos. Our AI agents extract text, understand visuals, and let you recall anything with natural language.
          </p>

          <div className="search-container">
            <form onSubmit={handleSearch}>
              <div className="search-input-wrap">
                <div className="search-icon">
                  {searching ? <Loader2 size={18} className="animate-spin" /> : <Search size={18} />}
                </div>
                <input
                  id="search-input"
                  type="text"
                  className="search-input"
                  placeholder="Try 'show my recipe' or 'code on dark background'..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
                <button type="submit" className="search-btn" disabled={searching}>
                  {searching ? 'Searching...' : 'Recall'}
                </button>
              </div>
            </form>
          </div>
        </motion.section>

        {/* ──── Results Section ──── */}
        <motion.section
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <div className="section-header">
            <div className="section-title">
              <div className={`icon-wrap ${results.length > 0 ? 'cyan' : 'violet'}`}>
                {results.length > 0 ? <Sparkles size={14} /> : <Layers size={14} />}
              </div>
              {results.length > 0
                ? `Found ${results.length} relevant memories`
                : 'Recent Memories'
              }
              <span className="section-count">{displayedMemories.length}</span>
            </div>
            {results.length > 0 && (
              <button
                className="btn-clear"
                onClick={() => { setResults([]); setQuery(''); setAiAnswer(''); setConfidenceMessage(''); setTopScore(0); }}
              >
                <X size={12} /> Clear
              </button>
            )}
          </div>

          {/* Agentic AI Response Card */}
            <AnimatePresence>
              {aiAnswer && (
                <motion.div 
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="ai-result-card"
                >
                  <div className="ai-result-header">
                    <div className="ai-badge">
                      <Sparkles size={14} className={topScore < 0.45 ? "text-amber-400" : "text-violet-400"} />
                      <span>{confidenceMessage || "Agentic Response"}</span>
                    </div>
                    <div className="ai-status">
                      {topScore >= 0.6 ? 'High Relevance' : topScore >= 0.35 ? 'Moderate Relevance' : 'Best Guess'}
                    </div>
                  </div>
                  
                  <div className="ai-result-text">
                    {aiAnswer}
                  </div>
                  
                  <div className="ai-result-footer">
                    <div className="ai-pipeline">
                      <div className="flex items-center gap-2">
                        <div className="dot violet"></div>
                        <span>Understanding</span>
                      </div>
                      <ChevronRight size={10} className="text-zinc-600" />
                      <div className="flex items-center gap-2">
                        <div className="dot cyan"></div>
                        <span>Retrieval</span>
                      </div>
                      <ChevronRight size={10} className="text-zinc-600" />
                      <div className="flex items-center gap-2">
                        <div className="dot emerald"></div>
                        <span>Synthesis</span>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

          {displayedMemories.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">
                <Brain size={32} />
              </div>
              <div className="empty-title">No memories yet</div>
              <p className="empty-text">
                Start building your visual memory bank. Upload a screenshot or photo and our AI agents will process it.
              </p>
            </div>
          ) : (
            <div className="memory-grid">
              {displayedMemories.map((memory, i) => (
                <motion.div
                  key={memory.id}
                  className="memory-card"
                  onClick={() => setSelectedMemory(memory)}
                  initial={{ opacity: 0, y: 24 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.06, duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
                >
                  <div className="card-image-wrap">
                    <img
                      src={memory.image_url}
                      alt="Visual memory"
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                    {memory.similarity != null && (
                      <div className={`match-badge ${getMatchClass(memory.similarity)}`}>
                        {Math.round(memory.similarity * 100)}% match
                      </div>
                    )}
                  </div>

                  <div className="card-body">
                    <p className="card-description">
                      {memory.image_description || 'Processing visual context with AI agents...'}
                    </p>
                    <div className="card-tags">
                      <span className="card-tag violet">
                        <Eye size={10} /> Vision AI
                      </span>
                      <span className="card-tag cyan">
                        <Cpu size={10} /> OCR
                      </span>
                      {memory.similarity != null && (
                        <span className="card-tag emerald">
                          <Sparkles size={10} /> Semantic
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="card-footer">
                    <div className="card-meta">
                      <Clock size={11} />
                      {formatDate(memory.created_at)}
                    </div>
                    <div className="card-action">
                      View Details <ChevronRight size={13} />
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </motion.section>
      </div>

      {/* ──── Detail Modal ──── */}
      <AnimatePresence>
        {selectedMemory && (
          <motion.div
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            onClick={() => setSelectedMemory(null)}
          >
            <motion.div
              className="modal-content"
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-image">
                <img src={selectedMemory.image_url} alt="Full memory" />
              </div>

              <div className="modal-details">
                <button className="modal-close" onClick={() => setSelectedMemory(null)}>
                  <X size={16} />
                </button>

                <div className="detail-section">
                  <div className="detail-label violet">
                    <Zap size={13} /> AI Visual Description
                  </div>
                  <p className="detail-text">
                    "{selectedMemory.image_description || 'No description available.'}"
                  </p>
                </div>

                {selectedMemory.extracted_text && (
                  <div className="detail-section">
                    <div className="detail-label emerald">
                      <Cpu size={13} /> OCR Extracted Text
                    </div>
                    <div className="detail-code">
                      {selectedMemory.extracted_text}
                    </div>
                  </div>
                )}

                {selectedMemory.similarity != null && (
                  <div className="detail-section">
                    <div className="detail-label cyan">
                      <Sparkles size={13} /> Similarity Score
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div style={{
                        flex: 1,
                        height: '6px',
                        borderRadius: '3px',
                        background: 'rgba(255,255,255,0.06)',
                        overflow: 'hidden'
                      }}>
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${Math.round(selectedMemory.similarity * 100)}%` }}
                          transition={{ duration: 0.8, ease: 'easeOut' }}
                          style={{
                            height: '100%',
                            borderRadius: '3px',
                            background: 'linear-gradient(90deg, var(--accent-violet), var(--accent-cyan))',
                          }}
                        />
                      </div>
                      <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                        {Math.round(selectedMemory.similarity * 100)}%
                      </span>
                    </div>
                  </div>
                )}

                <div className="detail-section">
                  <div className="detail-label violet">
                    <Layers size={13} /> Processing Pipeline
                  </div>
                  <div className="detail-badges">
                    <span className="detail-badge">
                      <Eye size={12} style={{ color: 'var(--accent-violet)' }} /> Vision Agent
                    </span>
                    <span className="detail-badge">
                      <Cpu size={12} style={{ color: 'var(--accent-emerald)' }} /> OCR Agent
                    </span>
                    <span className="detail-badge">
                      <Brain size={12} style={{ color: 'var(--accent-cyan)' }} /> Embedding Agent
                    </span>
                    <span className="detail-badge">
                      <Tag size={12} style={{ color: 'var(--accent-amber)' }} /> Tag Agent
                    </span>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

export default App;
