; Label-screen colour transforms
;
; One mix per palette.
; Each row makes one channel of the new colour, 0-31: (r*R + g*G + b*B + v*V) / 16 + offset from the game's colour (R, G, B, and V = the largest of them).
; So 16 is "1x", 8 is "half", 0 is "none"; offsets are added after.
;
; r    g    b    v  offset
label_logo_mix:                                 ; the logo: unchanged
        dc.w     16,   0,   0,   0,   0         ; red out
        dc.w      0,  16,   0,   0,   0         ; green out
        dc.w      0,   0,  16,   0,   0         ; blue out

label_bee_mix:                                  ; the bee mark: red and blue swapped
        dc.w      0,   0,  16,   0,   0         ; red out
        dc.w      0,  16,   0,   0,   0         ; green out
        dc.w     16,   0,   0,   0,   0         ; blue out

label_bg_mix:                                   ; the background: blue at its brightness
        dc.w      0,   0,   0,   8,   0         ; red out
        dc.w      0,   0,   0,  16,   0         ; green out
        dc.w      0,   0,   0,  32,   0         ; blue out
