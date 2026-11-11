; Recolour the startup logo, bee and background using label_col.inc.
; Palette entries use xRRRRRGGGGGBBBBB.

        include     "label_col.inc"

; Called each startup-screen frame.
; Generate the three palettes only once.
blue_label_palettes:
        cmpi.w      #BLUE_DONE,blue_pal_done
        beq         .done
        movem.l     d0-d7/a0-a2,-(sp)
        lea         logo_palette,a0
        lea         blue_logo_pal,a1
        lea         label_logo_mix,a2
        bsr         blue_pal_mix
        lea         bee_palette,a0
        lea         blue_bee_pal,a1
        lea         label_bee_mix,a2
        bsr         blue_pal_mix
        lea         label_bg_palette,a0
        lea         blue_bg_pal,a1
        lea         label_bg_mix,a2
        bsr         blue_pal_mix
        move.w      #BLUE_DONE,blue_pal_done
        movem.l     (sp)+,d0-d7/a0-a2
.done
        rts

; Transform 32 palette entries. a0 = source; a1 = destination; a2 = mix.
; Each output channel is (r*R + g*G + b*B + v*V) / 16 + offset.
; V is the largest source channel.
; Round down, clamp to 0-31 and preserve each entry's top bit.
blue_pal_mix:
        moveq       #32-1,d7
.colour
        move.w      (a0)+,d0
        move.w      d0,d3
        andi.w      #$001f,d3                   ; B
        move.w      d0,d2
        lsr.w       #5,d2
        andi.w      #$001f,d2                   ; G
        move.w      d0,d1
        lsr.w       #8,d1
        lsr.w       #2,d1
        andi.w      #$001f,d1                   ; R
        move.w      d1,d4                       ; V = the largest
        cmp.w       d2,d4
        bcc         .v1
        move.w      d2,d4
.v1
        cmp.w       d3,d4
        bcc         .v2
        move.w      d3,d4
.v2
        andi.w      #$8000,d0                   ; the top bit stays
        movea.l     a2,a3
        bsr         blue_mix_channel            ; red
        lsl.w       #8,d5
        lsl.w       #2,d5
        or.w        d5,d0
        bsr         blue_mix_channel            ; green
        lsl.w       #5,d5
        or.w        d5,d0
        bsr         blue_mix_channel            ; blue
        or.w        d5,d0
        move.w      d0,(a1)+
        dbra        d7,.colour
        rts

; Calculate one output channel in d5.
; Read five coefficients from a3 and advance a3 to the next channel.
blue_mix_channel:
        move.w      (a3)+,d5
        muls.w      d1,d5
        move.w      (a3)+,d6
        muls.w      d2,d6
        add.l       d6,d5
        move.w      (a3)+,d6
        muls.w      d3,d6
        add.l       d6,d5
        move.w      (a3)+,d6
        muls.w      d4,d6
        add.l       d6,d5
        asr.l       #4,d5                       ; /16, rounded down
        add.w       (a3)+,d5                    ; + offset
        bpl         .not_neg
        moveq       #0,d5
        rts
.not_neg
        cmpi.w      #31,d5
        bls         .in
        moveq       #31,d5
.in
        rts
