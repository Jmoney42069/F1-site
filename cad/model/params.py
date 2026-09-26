"""Single source of truth for dweilrobo dimensions (mm, g).

Evidence label per value:
  M = measured by us (caliper / scale)       -> may drive design
  D = datasheet / sourced listing            -> OK for concept, verify on arrival
  A = assumption / photo estimate            -> must NOT be frozen into printed parts
Coordinate frame: x forward, y left, z up, origin on the floor under the drive axle centre.
"""

EVIDENCE = {}


def p(name, value, evidence, note=""):
    EVIDENCE[name] = (value, evidence, note)
    return value


# --- body -------------------------------------------------------------------
BODY_D = p("BODY_D", 350, "A", "design choice, limited by rooms/furniture (unmeasured)")
PLATE_T = p("PLATE_T", 4, "A", "4 mm plywood or printed segments")
PLATE_Z = p("PLATE_Z", 45, "A", "underside of base plate")
WHEEL_WELL_CLEAR = p("WHEEL_WELL_CLEAR", 5, "A", "gap around wheel in plate cut-out")

# --- drive ------------------------------------------------------------------
WHEEL_D = p("WHEEL_D", 65, "A", "common 65 mm robot wheel, not bought yet")
WHEEL_W = p("WHEEL_W", 26, "A")
WHEEL_Y = p("WHEEL_Y", 135, "A", "wheel centre plane")
DRIVE_MOTOR_D = p("DRIVE_MOTOR_D", 25, "D", "JGA25-370 gearbox diameter")
DRIVE_MOTOR_L = p("DRIVE_MOTOR_L", 70, "A", "gearbox+motor+encoder, depends on ratio")
CASTER_X = p("CASTER_X", 150, "A")
CASTER_D = p("CASTER_D", 20, "A")

# --- mop pads (round, spinning) ---------------------------------------------
PAD_D = p("PAD_D", 130, "A", "self-made disc + microfiber")
PAD_H = p("PAD_H", 15, "A", "cloth + disc + hub stack")
PAD_X = p("PAD_X", -85, "A")
PAD_Y = p("PAD_Y", 68, "A")
MOP_MOTOR_L = p("MOP_MOTOR_L", 70, "A", "JGA25-370 vertical above plate")

# --- payload ------------------------------------------------------------------
TANK = p("TANK", dict(x=-5, y=0, lx=80, ly=100, h=50), "A", "~330 mL usable, over axle")
BATTERY = p("BATTERY", dict(x=-85, y=0, lx=60, ly=78, h=22), "A", "3S1P 18650 holder, behind axle for traction")
ELECTRONICS = p("ELECTRONICS", dict(x=90, y=0, lx=90, ly=110, h=30), "A")
DECK_Z = p("DECK_Z", 125, "A", "top deck underside")
LIDAR = p("LIDAR", dict(d=100, h=45), "A", "LDS02RR envelope, unverified")
