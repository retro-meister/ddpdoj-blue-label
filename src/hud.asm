; Stage-chain HUD: BRK beside each player’s life count
;
; The builder exports assets/hud/*.aseprite into unused sprite-ROM padding.
; The native sprite queue handles clipping and priority.

; Convert d6.w to four packed decimal digits.
; Preserves d0–d3.
blue_hud_decimal:
        movem.l     d0-d3,-(sp)
        moveq       #0,d0
        move.w      d6,d0
        moveq       #0,d1
        moveq       #0,d2
        moveq       #3,d3
.digit
        divu.w      #10,d0
        swap        d0
        move.w      d0,d6
        lsl.w       d2,d6
        or.w        d6,d1
        clr.w       d0
        swap        d0
        addq.w      #4,d2
        dbra        d3,.digit
        move.w      d1,d6
        movem.l     (sp)+,d0-d3
        rts

; Keep the final stage result on screen after the extend award clears the scoring tallies.
; A new stage or game resets the display for both players.
blue_hud_cache:
        move.w      sr,-(sp)
        movem.l     d0-d1,-(sp)
        move.w      stage_index,d0
        addq.w      #1,d0
        cmp.w       blue_hud_stage,d0
        beq         .copy
        move.w      d0,blue_hud_stage
        clr.l       blue_hud_flash_1
        clr.w       blue_hud_best_1
        clr.w       blue_hud_best_2
        clr.l       blue_hud_short_1
        clr.l       blue_hud_short_2
.copy
        move.w      blue_chain_1p,d0
        move.l      blue_short_1p,d1
        bne         .p1
        tst.w       d0
        beq         .p2
.p1
        cmp.l       blue_hud_short_1,d1
        bls         .copy1
        move.w      #BRK_FLASH_FRAMES,blue_hud_flash_1
.copy1
        move.w      d0,blue_hud_best_1
        move.l      d1,blue_hud_short_1
.p2
        move.w      blue_chain_2p,d0
        move.l      blue_short_2p,d1
        bne         .set2
        tst.w       d0
        beq         .end
.set2
        cmp.l       blue_hud_short_2,d1
        bls         .copy2
        move.w      #BRK_FLASH_FRAMES,blue_hud_flash_2
.copy2
        move.w      d0,blue_hud_best_2
        move.l      d1,blue_hud_short_2
.end
        movem.l     (sp)+,d0-d1
        move.w      (sp)+,ccr
        rts

blue_hud_frame:
        move.w      sr,-(sp)
        movem.l     d0-d7/a0-a3,-(sp)
        bsr         blue_hud_lives
        lea         blue_hud_flash_1,a2
        bsr         blue_hud_tick
        lea         blue_hud_flash_2,a2
        bsr         blue_hud_tick
        tst.w       demo_playing
        bne         .end
        bsr         blue_hud_cache
        tst.w       ships_1p
        bmi         .player2
        moveq       #0,d5
        bsr         blue_hud_row_position
        addi.w      #18*64,d1                   ; reserve two stock digits beside the life ship
        moveq       #0,d0
        move.w      blue_hud_best_1,d0
        move.l      blue_hud_short_1,d6
        lea         blue_hud_flash_1,a3
        bsr         blue_hud_panel
.player2
        tst.w       ships_2p
        bmi         .end
        moveq       #1,d5
        bsr         blue_hud_row_position
        subi.w      #48*64,d1                   ; mirrored box with fixed two-digit clearance
        moveq       #0,d0
        move.w      blue_hud_best_2,d0
        move.l      blue_hud_short_2,d6
        lea         blue_hud_flash_2,a3
        bsr         blue_hud_panel
.end
        movem.l     (sp)+,d0-d7/a0-a3
        move.w      (sp)+,ccr
        rts

blue_hud_tick:
        tst.w       (a2)
        beq         .end
        subq.w      #1,(a2)
.end
        rts

; d0: best, d6: short-chain sum, d1: frame position.
; Each player has an independent result; a3 points to its pulse timer.
; One glyph per digit fits the two-player queue, including during the pulse.
blue_hud_panel:
        movem.l     d0-d7/a0-a3,-(sp)
        cmpi.w      #12*(32-5),hud_sprite_bytes
        bhi         .end
        moveq       #0,d5
        cmpi.w      #CHAIN_THRESHOLD,d0
        bcs         .red
        cmp.l       d6,d0
        bls         .red
        moveq       #1,d5
.red
        lea         blue_hud_pictures,a2
        move.l      (a2),d2
        move.w      4(a2),d3
        moveq       #9,d4
        jsr         submit_hud_sprite
        cmpi.l      #9999,d6
        bls         .number
        move.l      #9999,d6
.number
        bsr         blue_hud_decimal
        moveq       #0,d7
        moveq       #0,d4
.colour
        tst.w       (a3)
        beq         .normal
        cmpi.w      #BRK_FLASH_FRAMES/2,(a3)
        bls         .fading
        lea         blue_hud_flash_numbers,a3
        bra         .draw
.fading
        lea         blue_hud_fade_numbers,a3
        bra         .draw
.normal
        lea         blue_hud_pictures+6,a3
        tst.w       d5
        beq         .draw
        adda.w      #240,a3
.draw
        addi.w      #14*64,d1
.digit
        rol.w       #4,d6
        move.w      d6,d0
        andi.w      #$f,d0
        bne         .visible
        cmpi.w      #3,d4
        beq         .visible
        tst.w       d7
        beq         .next
.visible
        moveq       #1,d7
        mulu.w      #6,d0
        lea         (a3,d0.w),a2
        move.l      (a2),d2
        move.w      4(a2),d3
        move.w      d4,-(sp)
        moveq       #9,d4
        jsr         submit_hud_sprite
        move.w      (sp)+,d4
.next
        adda.w      #60,a3
        addi.w      #6*64,d1
        addq.w      #1,d4
        cmpi.w      #4,d4
        bcs         .digit
.end
        movem.l     (sp)+,d0-d7/a0-a3
        rts

; d5: player.
; Return the native life counter's fixed-point position in d1.
; BRK shares this movement, including the boss bar and stage-clear return.
blue_hud_row_position:
        moveq       #24,d0
        moveq       #65,d2
        btst.b      #0,boss_flags+1
        beq         .entrance
        btst.b      #3,boss_flags
        bne         .returning
        move.w      life_slide_x,d0
        add.w       d0,d0
        addq.w      #8,d0
        move.w      life_slide_y,d2
        addi.w      #58,d2
        bra         .coordinates
.returning
        btst.b      #7,hud_phase+1              ; native stock has returned to its fixed text position
        bne         .coordinates
        sub.w       life_slide_x,d0
        sub.w       life_slide_y,d2
        bra         .coordinates
.entrance
        tst.w       hud_entering
        beq         .coordinates
        sub.w       hud_motion,d0
.coordinates
        tst.w       d5
        beq         .left
        neg.w       d0
        addi.w      #214,d0
.left
        lsl.w       #6,d0
        move.w      #432,d1                     ; hardware width minus this row's height
        sub.w       d2,d1
        lsl.w       #6,d1
        swap        d1
        move.w      d0,d1
        rts

; Keep xN beside the native single ship, including its separate boss move.
; Spare stock is display-only here; no life counter or extend rule is changed.
blue_hud_lives:
        moveq       #0,d5
.player
        move.w      ships_1p,d6
        tst.w       d5
        beq         .stock
        move.w      ships_2p,d6
.stock
        tst.w       d6
        bmi         .next
        cmpi.w      #12*(32-4),hud_sprite_bytes
        bhi         .next
        bsr         blue_hud_row_position
        tst.w       d6
        bne         .times
        move.l      d1,-(sp)
        move.w      hull_type_1p,d0
        tst.w       d5
        beq         .hull
        move.w      hull_type_2p,d0
.hull
        tst.w       d0
        sne         d0
        andi.w      #1,d0
        tst.w       d5
        beq         .icon_left
        addq.w      #2,d0
        addi.w      #10*64,d1
        bra         .icon
.icon_left
        subi.w      #8*64,d1
.icon
        mulu.w      #6,d0
        lea         blue_hud_ship_icons,a2
        adda.w      d0,a2
        move.l      (a2),d2
        move.w      4(a2),d3
        move.w      d5,d4
        jsr         submit_hud_sprite
        move.l      (sp)+,d1
.times
        tst.w       d5
        beq         .stock_width
        subi.w      #6*64,d1                    ; grow toward the centre, clear of P2 ship
.stock_width
        lea         blue_hud_times,a2
        move.l      (a2),d2
        move.w      4(a2),d3
        moveq       #9,d4
        jsr         submit_hud_sprite
        addi.w      #4*64,d1
        move.w      d6,d0
        cmpi.w      #10,d0
        bcs         .units
        moveq       #0,d7
        move.w      d0,d7
        divu.w      #10,d7
        move.w      d7,d0
        bsr         blue_hud_life_digit
        addi.w      #6*64,d1
        swap        d7
        move.w      d7,d0
.units
        bsr         blue_hud_life_digit
.next
        addq.w      #1,d5
        cmpi.w      #2,d5
        bcs         .player
        rts

blue_hud_life_digit:
        mulu.w      #6,d0
        lea         blue_hud_life_numbers,a2
        adda.w      d0,a2
        move.l      (a2),d2
        move.w      4(a2),d3
        moveq       #9,d4
        jmp         submit_hud_sprite
