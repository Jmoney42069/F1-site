'use client'

import { useEffect, useRef, useState } from 'react'
import styles from './page.module.css'

const TOTAL_FRAMES = 121

function pad(n) {
  return String(n).padStart(4, '0')
}

export default function Home() {
  const canvasRef = useRef(null)
  const sectionRef = useRef(null)
  const framesRef = useRef([])
  const currentFrameRef = useRef(0)

  const [loadedCount, setLoadedCount] = useState(0)
  const [phase, setPhase] = useState('loading') // loading | entering | scrolling | done
  const [assemblyDone, setAssemblyDone] = useState(false)
  const autoScrollRaf = useRef(null)
  const allLoadedRef = useRef(false)

  // ── Preload all frames ──────────────────────────────
  useEffect(() => {
    let loaded = 0
    const images = new Array(TOTAL_FRAMES)

    for (let i = 1; i <= TOTAL_FRAMES; i++) {
      const img = new Image()
      img.src = `/frames/frame_${pad(i)}.jpg`
      img.onload = () => {
        loaded++
        setLoadedCount(loaded)
        if (loaded === TOTAL_FRAMES) {
          allLoadedRef.current = true
          framesRef.current = images
          drawFrame(0)

          // Loading done → start sequence
          setTimeout(() => setPhase('entering'), 400)
          setTimeout(() => {
            setPhase('scrolling')
            startAutoScroll()
          }, 1400)
        }
      }
      images[i - 1] = img
    }
  }, [])

  // ── Draw a specific frame to canvas ────────────────
  const drawFrame = (index) => {
    const canvas = canvasRef.current
    const img = framesRef.current[index]
    if (!canvas || !img) return

    const ctx = canvas.getContext('2d')
    const dpr = window.devicePixelRatio || 1
    const w = canvas.clientWidth
    const h = canvas.clientHeight

    if (canvas.width !== w * dpr || canvas.height !== h * dpr) {
      canvas.width = w * dpr
      canvas.height = h * dpr
      ctx.scale(dpr, dpr)
    }

    // Fill background first so grey extends seamlessly beyond image
    ctx.fillStyle = '#e8e8e8'
    ctx.fillRect(0, 0, w, h)

    // Object-fit: contain — shows full image, no cropping on any screen size
    const imgRatio = img.naturalWidth / img.naturalHeight
    const canvasRatio = w / h
    let dw, dh, dx, dy

    if (imgRatio > canvasRatio) {
      // Landscape image in portrait viewport — fit by width
      dw = w; dh = w / imgRatio
      dx = 0; dy = (h - dh) / 2
    } else {
      // Portrait image in landscape viewport — fit by height
      dh = h; dw = h * imgRatio
      dx = (w - dw) / 2; dy = 0
    }

    ctx.drawImage(img, dx, dy, dw, dh)
  }

  // ── Auto scroll through the sequence ───────────────
  const startAutoScroll = () => {
    const section = sectionRef.current
    if (!section) return

    const totalScrollable = section.offsetHeight - window.innerHeight
    const duration = 5000
    const start = performance.now()

    const step = (now) => {
      const t = Math.min((now - start) / duration, 1)
      // Ease in-out cubic
      const eased = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2
      window.scrollTo(0, eased * totalScrollable)

      if (t < 1) {
        autoScrollRaf.current = requestAnimationFrame(step)
      } else {
        setAssemblyDone(true)
        setPhase('done')
      }
    }

    autoScrollRaf.current = requestAnimationFrame(step)
  }

  // ── RAF loop: scroll → frame index → canvas ────────
  useEffect(() => {
    let rafId
    let lastFrame = -1

    const tick = () => {
      const section = sectionRef.current
      if (allLoadedRef.current && section) {
        const rect = section.getBoundingClientRect()
        const totalScrollable = section.offsetHeight - window.innerHeight
        const p = Math.max(0, Math.min(1, -rect.top / totalScrollable))
        const frameIndex = Math.min(
          Math.round(p * (TOTAL_FRAMES - 1)),
          TOTAL_FRAMES - 1
        )

        if (frameIndex !== lastFrame) {
          drawFrame(frameIndex)
          lastFrame = frameIndex
          currentFrameRef.current = frameIndex
        }
      }
      rafId = requestAnimationFrame(tick)
    }

    rafId = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafId)
  }, [])

  // ── Resize handler ──────────────────────────────────
  useEffect(() => {
    const onResize = () => drawFrame(currentFrameRef.current)
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  const loadPct = Math.round((loadedCount / TOTAL_FRAMES) * 100)
  const scrollPct = Math.round((currentFrameRef.current / (TOTAL_FRAMES - 1)) * 100)

  return (
    <main className={styles.main}>

      {/* ── LOADING SCREEN ─────────────────────────────── */}
      <div className={`${styles.loader} ${phase !== 'loading' ? styles.loaderHide : ''}`}>
        <div className={styles.loaderContent}>
          <p className={styles.loaderLabel}>FORMULA 1</p>
          <h1 className={styles.loaderName}>Joaquin Herman</h1>
          <div className={styles.loaderBarWrap}>
            <div className={styles.loaderBar} style={{ width: `${loadPct}%` }} />
          </div>
          <p className={styles.loaderPct}>{loadPct}%</p>
        </div>
      </div>

      {/* ── NAV ────────────────────────────────────────── */}
      <nav className={`${styles.nav} ${assemblyDone ? styles.navVisible : ''}`}>
        <div className={styles.navInner}>
          <span className={styles.navLogo}>F1</span>
          <ul className={styles.navLinks}>
            <li><a href="#cars">Cars</a></li>
            <li><a href="#technology">Technology</a></li>
            <li><a href="#team">Team</a></li>
            <li><a href="#schedule">Schedule</a></li>
          </ul>
          <button className={styles.navCta}>Enter Season</button>
        </div>
      </nav>

      {/* ── SCROLL SEQUENCE ────────────────────────────── */}
      <section ref={sectionRef} className={styles.scrollSection}>
        <div className={styles.stickyContainer}>
          <canvas ref={canvasRef} className={styles.assemblyCanvas} />

          {/* Red progress line */}
          <div className={styles.progressBar}>
            <div className={styles.progressFill} style={{ width: `${scrollPct}%` }} />
          </div>

          {/* ASSEMBLY COMPLETE text fades in at the end */}
          <div
            className={styles.completeOverlay}
            style={{
              opacity: scrollPct > 85 ? (scrollPct - 85) / 15 : 0,
              pointerEvents: 'none'
            }}
          >
            <span className={styles.completeText}>ASSEMBLY COMPLETE</span>
          </div>
        </div>
      </section>

      {/* ── SITE CONTENT ───────────────────────────────── */}
      <div className={`${styles.siteContent} ${assemblyDone ? styles.siteContentVisible : ''}`}>

        <section id="cars" className={styles.carsSection}>
          <div className={styles.sectionInner}>
            <p className={styles.sectionLabel}>2025 SEASON</p>
            <h2 className={styles.sectionTitle}>The Machine</h2>
            <div className={styles.statsGrid}>
              {[
                { label: 'Power Unit', value: '1000+', unit: 'HP' },
                { label: 'Top Speed', value: '375', unit: 'km/h' },
                { label: 'Weight', value: '798', unit: 'kg' },
                { label: '0–100', value: '2.6', unit: 'sec' },
              ].map((stat) => (
                <div key={stat.label} className={styles.statCard}>
                  <span className={styles.statValue}>{stat.value}<sup>{stat.unit}</sup></span>
                  <span className={styles.statLabel}>{stat.label}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="technology" className={styles.techSection}>
          <div className={styles.sectionInner}>
            <p className={styles.sectionLabel}>ENGINEERING</p>
            <h2 className={styles.sectionTitle}>Built Different</h2>
            <div className={styles.techGrid}>
              {[
                { title: 'Aerodynamics', desc: 'Over 20,000 components generating more downforce than the car weighs at 200 km/h.', num: '01' },
                { title: 'Power Unit', desc: '1.6L V6 hybrid delivering over 1000 horsepower with thermal efficiency above 50%.', num: '02' },
                { title: 'Carbon Fiber', desc: 'Monocoque chassis lighter than a bicycle frame, yet survives 50G crash impacts.', num: '03' },
              ].map((item) => (
                <div key={item.num} className={styles.techCard}>
                  <span className={styles.techNum}>{item.num}</span>
                  <h3 className={styles.techTitle}>{item.title}</h3>
                  <p className={styles.techDesc}>{item.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="team" className={styles.teamSection}>
          <div className={styles.sectionInner}>
            <p className={styles.sectionLabel}>THE DRIVERS</p>
            <h2 className={styles.sectionTitle}>Behind The Wheel</h2>
            <div className={styles.driverGrid}>
              {[
                { number: '5', name: 'Nico Hülkenberg', team: 'Sauber Audi F1 Team' },
                { number: '27', name: 'Gabriel Bortoleto', team: 'Sauber Audi F1 Team' },
              ].map((driver) => (
                <div key={driver.number} className={styles.driverCard}>
                  <span className={styles.driverNumber}>{driver.number}</span>
                  <div className={styles.driverInfo}>
                    <span className={styles.driverName}>{driver.name}</span>
                    <span className={styles.driverTeam}>{driver.team}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <footer className={styles.footer}>
          <div className={styles.footerInner}>
            <span className={styles.footerLogo}>F1</span>
            <span className={styles.footerCopy}>© 2025 Formula One. All rights reserved.</span>
          </div>
        </footer>
      </div>
    </main>
  )
}
