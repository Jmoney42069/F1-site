'use client'

import { useEffect, useRef, useState } from 'react'
import styles from './page.module.css'

export default function Home() {
  const videoRef = useRef(null)
  const sectionRef = useRef(null)
  const [phase, setPhase] = useState('loading') // loading | entering | scrolling | done
  const [loadPct, setLoadPct] = useState(0)
  const [scrollProgress, setScrollProgress] = useState(0)
  const [assemblyDone, setAssemblyDone] = useState(false)
  const videoReadyRef = useRef(false)
  const autoScrollRaf = useRef(null)

  // Animate loading bar to ~80% while waiting for video
  useEffect(() => {
    let val = 0
    const interval = setInterval(() => {
      val += Math.random() * 4
      if (val >= 80) { clearInterval(interval); val = 80 }
      setLoadPct(Math.min(val, 80))
    }, 60)
    return () => clearInterval(interval)
  }, [])

  // Load video, then kick off the sequence
  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    const onReady = () => {
      if (videoReadyRef.current) return
      videoReadyRef.current = true
      video.pause()
      video.currentTime = 0

      // Fill bar to 100%, then fade out loading screen
      setLoadPct(100)
      setTimeout(() => setPhase('entering'), 500)
      setTimeout(() => {
        setPhase('scrolling')
        startAutoScroll()
      }, 1400)
    }

    video.addEventListener('canplay', onReady)
    video.addEventListener('loadedmetadata', onReady)
    video.load()

    return () => {
      video.removeEventListener('canplay', onReady)
      video.removeEventListener('loadedmetadata', onReady)
    }
  }, [])

  const startAutoScroll = () => {
    const section = sectionRef.current
    if (!section) return

    const totalScrollable = section.offsetHeight - window.innerHeight
    const duration = 5500
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

  // RAF loop — maps scroll position → video.currentTime at display refresh rate
  useEffect(() => {
    let rafId

    const tick = () => {
      const video = videoRef.current
      const section = sectionRef.current

      if (videoReadyRef.current && video?.duration && section) {
        const rect = section.getBoundingClientRect()
        const totalScrollable = section.offsetHeight - window.innerHeight
        const p = Math.max(0, Math.min(1, -rect.top / totalScrollable))

        setScrollProgress(p)

        const target = p * video.duration
        if (Math.abs(video.currentTime - target) > 0.01) {
          if ('fastSeek' in video) video.fastSeek(target)
          else video.currentTime = target
        }
      }

      rafId = requestAnimationFrame(tick)
    }

    rafId = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafId)
  }, [])

  return (
    <main className={styles.main}>

      {/* ── LOADING SCREEN ───────────────────────── */}
      <div className={`${styles.loader} ${phase !== 'loading' ? styles.loaderHide : ''}`}>
        <div className={styles.loaderContent}>
          <p className={styles.loaderLabel}>FORMULA 1</p>
          <h1 className={styles.loaderName}>Joaquin Herman</h1>
          <div className={styles.loaderBarWrap}>
            <div className={styles.loaderBar} style={{ width: `${loadPct}%` }} />
          </div>
          <p className={styles.loaderPct}>{Math.round(loadPct)}%</p>
        </div>
      </div>

      {/* ── NAV — appears when assembly done ─────── */}
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

      {/* ── SCROLL SEQUENCE ──────────────────────── */}
      <section ref={sectionRef} className={styles.scrollSection}>
        <div className={styles.stickyContainer}>
          <div className={styles.bgGradient} />

          <video
            ref={videoRef}
            className={styles.assemblyVideo}
            src="/assembly.mp4"
            muted
            autoPlay
            playsInline
            preload="auto"
          />

          {/* Progress bar */}
          <div className={styles.progressBar}>
            <div className={styles.progressFill} style={{ width: `${scrollProgress * 100}%` }} />
          </div>

          {/* Assembly complete flash */}
          <div
            className={styles.completeOverlay}
            style={{
              opacity: scrollProgress > 0.85 ? (scrollProgress - 0.85) / 0.15 : 0,
              pointerEvents: 'none'
            }}
          >
            <span className={styles.completeText}>ASSEMBLY COMPLETE</span>
          </div>
        </div>
      </section>

      {/* ── SITE CONTENT ─────────────────────────── */}
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
