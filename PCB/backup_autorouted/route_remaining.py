"""Route the remaining CoffeeGrinder nets on top of the user's placement.
usage: python.exe route.py <in.kicad_pcb> <out.kicad_pcb>
"""
import sys
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
MM = pcbnew.FromMM
F, B = pcbnew.F_Cu, pcbnew.B_Cu
nets = b.GetNetsByName()


def net(name):
    n = nets[name]
    assert n is not None and n.GetNetCode() > 0, name
    return n


def P(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def path(netname, layer, width, pts):
    for a, c in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(P(*a)); t.SetEnd(P(*c))
        t.SetWidth(MM(width)); t.SetLayer(layer); t.SetNet(net(netname))
        b.Add(t)


def via(netname, x, y, d=0.6, drill=0.3):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(P(x, y)); v.SetWidth(MM(d)); v.SetDrill(MM(drill))
    v.SetLayerPair(F, B); v.SetNet(net(netname))
    b.Add(v)


# ---------------- +12V ----------------
# main bus D2/Q1 -> past R1 -> down beside D1 -> D1 K   (0.8 mm: channel between R1 and C4/C5)
path('+12V', F, 0.8, [(67.438, 74.5), (67.2, 74.74), (67.2, 76.9), (61.6, 76.9), (61.6, 83.0), (60.0, 83.0)])
# D1 K -> C1+ and D3 K (motor supply, 1.0 mm)
path('+12V', F, 1.0, [(60.0, 83.0), (60.0, 85.0), (54.0, 85.0), (54.0, 88.5)])
path('+12V', F, 1.0, [(54.0, 85.0), (52.5, 85.0), (52.5, 82.75)])
# regulator branch: bus -> U2 pin 3, C3, C2 (0.5 mm)
path('+12V', F, 0.5, [(61.6, 83.0), (69.35, 83.0), (70.35, 83.6)])
path('+12V', F, 0.5, [(69.35, 83.0), (69.35, 80.5)])
path('+12V', F, 0.5, [(70.35, 83.6), (70.525, 85.9)])
# divider top R8 pad 1
path('+12V', F, 0.3, [(67.438, 74.5), (68.6, 74.5), (70.3, 72.8), (71.4, 71.7), (71.4, 70.425)])
# TP1 from C2
path('+12V', F, 0.4, [(70.525, 85.9), (70.525, 87.3), (76.6, 87.3), (76.6, 92.6), (78.8, 92.6), (80.0, 93.8), (80.0, 95.5)])

# ---------------- +3V3 ----------------
path('+3V3', F, 0.4, [(69.35, 77.5), (68.2, 77.5), (68.2, 79.95), (66.8, 79.95), (64.5, 79.775)])
# up to the module: B.Cu jumper U2 -> C12
via('+3V3', 70.5, 76.4)
path('+3V3', F, 0.4, [(70.5, 76.4), (69.35, 77.5)])
via('+3V3', 70.5, 66.3)
path('+3V3', B, 0.4, [(70.5, 76.4), (70.5, 66.3)])
path('+3V3', F, 0.4, [(70.5, 66.3), (71.425, 66.3)])
path('+3V3', F, 0.4, [(75.43, 65.765), (74.3, 65.765), (73.85, 65.22), (71.425, 65.22), (71.425, 66.3)])
path('+3V3', F, 0.4, [(71.425, 65.22), (71.25, 64.62), (71.25, 63.9)])
# down to U3/C8: B.Cu jumper
path('+3V3', B, 0.4, [(70.5, 76.4), (70.5, 91.9), (73.45, 91.9), (73.45, 92.25)])
via('+3V3', 73.45, 92.25)
path('+3V3', F, 0.3, [(73.45, 92.25), (72.638, 93.06), (72.638, 94.05)])
# C8 -> TP2 -> J4 pin 1
path('+3V3', F, 0.4, [(74.5, 94.775), (74.5, 95.8), (75.0, 96.3), (75.0, 97.3), (84.8, 97.3), (84.8, 99.5)])
path('+3V3', F, 0.4, [(82.5, 97.3), (82.5, 95.5)])
# J4 pin 1 -> J3 pin 1 on B.Cu (both THT)
path('+3V3', B, 0.4, [(84.8, 99.5), (86.7, 97.6), (86.7, 89.3), (93.0, 89.3), (93.0, 86.0)])
# R12 -> J3 pin 1
path('+3V3', F, 0.3, [(96.0, 89.825), (94.6, 89.825), (93.0, 88.225), (93.0, 86.0)])

# ---------------- VIN_SENSE ----------------
path('/VIN_SENSE', F, 0.25, [(71.4, 68.775), (73.3, 70.425)])
path('/VIN_SENSE', F, 0.25, [(73.3, 70.425), (73.45, 70.575), (73.45, 73.45), (72.925, 73.975), (72.4, 73.975)])
path('/VIN_SENSE', F, 0.25, [(75.43, 68.305), (74.15, 68.305), (74.15, 69.95), (73.68, 70.425), (73.3, 70.425)])

# ---------------- module left-side signals: vias inboard, B.Cu lanes ----------------
# I_SENSE  (pin 17) lane x=75.1 -> via near C9 -> C9 pin 1 and TP4
via('/I_SENSE', 77.0, 67.035)
path('/I_SENSE', F, 0.25, [(75.43, 67.035), (77.0, 67.035)])
path('/I_SENSE', B, 0.25, [(77.0, 67.035), (75.1, 67.035), (75.1, 87.9), (74.8, 88.2)])
via('/I_SENSE', 74.8, 88.2)
path('/I_SENSE', F, 0.25, [(74.8, 88.2), (75.5, 88.9), (75.5, 90.9), (75.125, 91.275), (74.5, 91.275)])
path('/I_SENSE', F, 0.25, [(75.5, 90.9), (75.5, 94.0), (76.4, 94.9), (77.0, 95.5)])
# MOTOR_PWM (pin 19) lane x=75.65 -> via next to TP6
via('/MOTOR_PWM', 77.0, 69.575)
path('/MOTOR_PWM', F, 0.25, [(75.43, 69.575), (77.0, 69.575)])
path('/MOTOR_PWM', B, 0.25, [(77.0, 69.575), (75.65, 69.575), (75.65, 98.5), (72.0, 98.5), (71.5, 99.0), (71.5, 100.5)])
via('/MOTOR_PWM', 71.5, 100.5)
path('/MOTOR_PWM', F, 0.25, [(71.5, 100.5), (70.0, 100.5)])
# UART_RX (pin 23) lane x=76.2 -> J4 pin 3 (THT)
via('/UART_RX', 77.0, 74.655)
path('/UART_RX', F, 0.25, [(75.43, 74.655), (77.0, 74.655)])
path('/UART_RX', B, 0.25, [(77.0, 74.655), (76.2, 74.655), (76.2, 97.0), (79.72, 97.0), (79.72, 99.5)])
# UART_TX (pin 21) east lane x=81.3 between J5 and J3 -> J4 pin 2 (THT)
via('/UART_TX', 77.0, 72.115)
path('/UART_TX', F, 0.25, [(75.43, 72.115), (77.0, 72.115)])
path('/UART_TX', B, 0.25, [(77.0, 72.115), (81.3, 72.115), (81.3, 97.5), (82.26, 98.46), (82.26, 99.5)])
# LID_SW (pin 29) on B.Cu straight down to J5 pin 1 (THT)
via('/LID_SW', 78.45, 79.95)
path('/LID_SW', F, 0.25, [(78.45, 81.5), (78.45, 79.95)])
path('/LID_SW', B, 0.25, [(78.45, 79.95), (78.45, 89.6), (78.0, 90.05), (78.0, 90.5)])
# BTN (pin 26) on F.Cu: through the U2/module gap, under the module edge, between J5 and J3
path('/BTN', F, 0.25, [(75.43, 78.465), (74.0, 78.465), (74.0, 83.3), (80.5, 83.3), (81.25, 84.05),
                       (81.25, 92.5), (87.5, 92.5), (89.0, 94.0)])
path('/BTN', F, 0.25, [(89.0, 94.0), (95.5, 94.0)])

# ---------------- SWD / LED ----------------
path('/nRESET', F, 0.25, [(87.34, 81.5), (87.34, 83.5), (85.38, 85.46), (85.38, 86.0)])
path('/SWDCLK', F, 0.25, [(88.61, 81.5), (88.61, 85.31), (87.92, 86.0)])
path('/SWDIO', F, 0.25, [(89.88, 81.5), (89.88, 85.42), (90.46, 86.0)])
path('/LED_K', F, 0.25, [(93.69, 81.5), (93.69, 82.6), (95.3, 84.213), (96.0, 84.213)])
path('Net-(D4-A)', F, 0.25, [(96.0, 85.787), (96.0, 88.175)])

# ---------------- GND stitching to the bottom plane ----------------
path('GND', F, 0.4, [(73.15, 63.9), (77.18, 64.0)])                  # C11 -> module GND pin 15
path('GND', F, 0.3, [(73.3, 68.775), (73.3, 67.55), (72.975, 66.3)])  # R9 -> C12 GND
via('GND', 73.3, 67.55)
via('GND', 72.4, 71.6); path('GND', F, 0.3, [(72.4, 71.6), (72.4, 72.425)])          # C10
via('GND', 65.5, 78.1); path('GND', F, 0.4, [(64.5, 78.225), (65.5, 78.1), (66.8, 78.05)])  # C5/C4
via('GND', 61.15, 75.6); path('GND', F, 0.3, [(61.15, 75.6), (62.175, 75.8)])        # R1
via('GND', 58.4, 78.6); via('GND', 58.4, 79.6)                                    # D1 anode
path('GND', F, 0.6, [(58.4, 78.6), (60.0, 79.0), (58.4, 79.6)])
via('GND', 72.2, 77.4); via('GND', 72.2, 80.7)                                    # U2 tab
path('GND', F, 0.4, [(72.2, 77.4), (72.2, 79.0), (72.2, 80.7)])
via('GND', 73.1, 84.75); path('GND', F, 0.3, [(72.25, 83.6), (73.1, 84.75), (72.075, 85.9)])  # C3/C2
via('GND', 73.5, 89.5); path('GND', F, 0.3, [(73.5, 89.5), (74.5, 89.725)])          # C9
via('GND', 73.55, 93.15); path('GND', F, 0.3, [(74.5, 93.225), (73.55, 93.15)])      # C8
via('GND', 69.2, 95.0); path('GND', F, 0.3, [(70.362, 95.0), (69.2, 95.0)])          # U3 GND
via('GND', 61.3, 100.2); path('GND', F, 0.3, [(62.175, 100.0), (61.3, 100.2)])       # R5
via('GND', 66.9, 92.3, 0.8, 0.4); via('GND', 67.95, 92.3, 0.8, 0.4)              # shunt return
path('GND', F, 0.8, [(66.9, 92.3), (67.5, 93.537), (67.95, 92.3)])
via('GND', 85.0, 93.9); path('GND', F, 0.3, [(85.0, 93.9), (85.0, 95.5)])            # TP3
via('GND', 77.18, 65.5)                                                           # module pin 15
via('GND', 96.23, 80.0); via('GND', 97.5, 80.0)                                   # module pins 42/43
path('GND', F, 0.3, [(96.23, 81.5), (96.23, 80.0)]); path('GND', F, 0.3, [(97.5, 81.5), (97.5, 80.0)])
via('GND', 93.69, 65.5); via('GND', 96.23, 65.5)                                  # module pins 2/1
path('GND', F, 0.3, [(93.69, 64.0), (93.69, 65.5)]); path('GND', F, 0.3, [(96.23, 64.0), (96.23, 65.5)])
path('GND', F, 0.3, [(96.23, 64.0), (97.5, 64.0)])

# ---------------- GND pours, both layers ----------------
for layer, prio in ((B, 0), (F, 0)):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer); z.SetNet(net('GND'))
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(MM(0.3))
    z.SetMinThickness(MM(0.25))
    z.SetThermalReliefGap(MM(0.4))
    z.SetThermalReliefSpokeWidth(MM(0.5))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline(); o.NewOutline()
    for x, y in ((50.3, 62.3), (104.7, 62.3), (104.7, 101.7), (50.3, 101.7)):
        o.Append(MM(x), MM(y))
    b.Add(z)

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[2])
print('saved', sys.argv[2])
