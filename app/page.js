'use client'

import { useEffect, useRef, useState } from 'react'
import styles from './page.module.css'

export default function Home() {
  const videoRef = useRef(null)
  const sectionRef = useRef(null)
  const [assemblyDone, setAssemblyDone] = useState(false)
  const [progress, setProgress] = useState(0)
  const [videoReady, setVideoReady] = useState(false)
  const videoReadyRef = useRef(false)
  const assemblyDoneRef = useRef(false)

  useEffect(() => {
    const video = videoRef.current
    const section = sectionRef.current
    if (!video || !section) return

    let targetProgress = 0
    let rafId = null

    // RAF loop — decouples scroll input from seeking, runs at display refresh rate
    const tick = () => {
      if (videoReadyRef.current && video.duration) {
        const targetTime = targetProgress * video.duration
        const delta = Math.abs(video.currentTime - targetTime)
        if (delta > 0.01) {
          if ('fastSeek' in video) {
            video.fastSeek(targetTime)
          } else {
            video.currentTime = targetTime
          }
        }
      }
      rafId = requestAnimationFrame(tick)
    }

    const handleScroll = () => {
      const rect = section.getBoundingClientRect()
      const totalScrollable = section.offsetHeight - window.innerHeight
      const scrolled = -rect.top
      const p = Math.max(0, Math.min(1, scrolled / totalScrollable))

      targetProgress = p
      setProgress(p)

      if (p >= 0.98 && !assemblyDoneRef.current) {
        assemblyDoneRef.current = true
        setAssemblyDone(true)
      }
    }

    const markReady = () => {
      if (videoReadyRef.current) return
      video.pause()
      video.currentTime = 0
      videoReadyRef.current = true
      setVideoReady(true)
    }

    video.addEventListener('loadedmetadata', markReady)
    video.addEventListener('canplay', markReady)
    video.load()

    rafId = requestAnimationFrame(tick)
    window.addEventListener('scroll', handleScroll, { passive: true })

    return () => {
      cancelAnimationFrame(rafId)
      window.removeEventListener('scroll', handleScroll)
      video.removeEventListener('loadedmetadata', markReady)
      video.removeEventListener('canplay', markReady)
    }
  }, [])

  return (
    <main className={styles.main}>
      {/* NAV — locked until assembly done */}
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

      {/* SCROLL SEQUENCE SECTION */}
      <section ref={sectionRef} className={styles.scrollSection}>
        <div className={styles.stickyContainer}>

          {/* Background gradient that shifts with progress */}
          <div
            className={styles.bgGradient}
            style={{ opacity: 1 - progress * 0.3 }}
          />

          {/* Video */}
          <video
            ref={videoRef}
            className={styles.assemblyVideo}
            src="/assembly.mp4"
            muted
            autoPlay
            playsInline
            preload="auto"
          />

          {/* Fallback overlay when video not loaded */}
          {!videoReady && (
            <div className={styles.videoFallback}>
              <div className={styles.fallbackText}>
                <span className={styles.fallbackLine}>assembly.</span>
                <span className={styles.fallbackSub}>Add assembly.mp4 to /public</span>
              </div>
            </div>
          )}

          {/* Progress indicator */}
          <div className={styles.progressBar}>
            <div
              className={styles.progressFill}
              style={{ width: `${progress * 100}%` }}
            />
          </div>

          {/* Scroll hint — fades out as user scrolls */}
          <div
            className={styles.scrollHint}
            style={{ opacity: Math.max(0, 1 - progress * 8) }}
          >
            <span>SCROLL TO ASSEMBLE</span>
            <div className={styles.scrollArrow} />
          </div>

          {/* Assembly complete overlay */}
          <div
            className={styles.completeOverlay}
            style={{
              opacity: progress > 0.85 ? (progress - 0.85) / 0.15 : 0,
              pointerEvents: 'none'
            }}
          >
            <span className={styles.completeText}>ASSEMBLY COMPLETE</span>
          </div>
        </div>
      </section>

      {/* REST OF SITE — unlocks after assembly */}
      <div className={`${styles.siteContent} ${assemblyDone ? styles.siteContentVisible : ''}`}>

        {/* CARS SECTION */}
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

        {/* TECHNOLOGY SECTION */}
        <section id="technology" className={styles.techSection}>
          <div className={styles.sectionInner}>
            <p className={styles.sectionLabel}>ENGINEERING</p>
            <h2 className={styles.sectionTitle}>Built Different</h2>
            <div className={styles.techGrid}>
              {[
                {
                  title: 'Aerodynamics',
                  desc: 'Over 20,000 components generating more downforce than the car weighs at 200 km/h.',
                  num: '01'
                },
                {
                  title: 'Power Unit',
                  desc: '1.6L V6 hybrid delivering over 1000 horsepower with thermal efficiency above 50%.',
                  num: '02'
                },
                {
                  title: 'Carbon Fiber',
                  desc: 'Monocoque chassis lighter than a bicycle frame, yet survives 50G crash impacts.',
                  num: '03'
                },
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

        {/* TEAM SECTION */}
        <section id="team" className={styles.teamSection}>
          <div className={styles.sectionInner}>
            <p className={styles.sectionLabel}>THE DRIVERS</p>
            <h2 className={styles.sectionTitle}>Behind The Wheel</h2>
            <div className={styles.driverGrid}>
              {[
                { number: '5', name: 'Nico Hülkenberg', team: 'Sauber Audi F1 Team' },
                { number: '27', name: 'Nico Hülkenberg', team: 'Reserve' },
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

        {/* FOOTER */}
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
