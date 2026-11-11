; Chain extends
;
; Award an extra life when the best pre-boss chain beats the sum of completed chains below CHAIN_THRESHOLD.
; Award at stage clear, except stage 5: award when Jetbachi dies, before Hibachi appears.

; At a new game, clear both players' chain tallies and reset the HUD state.
blue_chain_clear:
        clr.l       blue_hud_flash_1
        clr.w       blue_hud_stage
        clr.l       blue_short_1p
        clr.l       blue_short_2p
        clr.w       blue_chain_boss
        clr.w       blue_chain_1p
        clr.w       blue_chain_2p
        rts

; Each frame before the boss appears, update each player's best stage chain.
blue_chain_frame:
        move.w      stage_index,d0
        addq.w      #1,d0
        cmp.w       blue_chain_boss,d0
        beq         .end
        btst.b      #0,boss_flags
        bne         .end
        move.w      chain_1p,d0
        bsr         blue_chain_number
        cmp.w       blue_chain_1p,d0
        bls         .p2
        move.w      d0,blue_chain_1p
.p2
        move.w      chain_2p,d0
        bsr         blue_chain_number
        cmp.w       blue_chain_2p,d0
        bls         .end
        move.w      d0,blue_chain_2p
.end
        rts

; When the boss appears, record any running chains and freeze both tallies.
; Keep stage 5 frozen through all three boss forms.
blue_chain_boss_last:
blue_chain_boss_start:
        move.w      sr,-(sp)
        movem.l     d0-d1/a0-a1,-(sp)
        bsr         blue_chain_stop_1p
        bsr         blue_chain_stop_2p
        move.w      stage_index,d0
        addq.w      #1,d0
        move.w      d0,blue_chain_boss
        movem.l     (sp)+,d0-d1/a0-a1
        move.w      (sp)+,ccr
        rts

; When a bomb or respawn ends a chain, record it only if its timer is running.
; An expired chain has already been counted.
blue_chain_stop_1p:
        tst.w       chain_timer_1p
        beq         .end
        bsr         blue_chain_end_1p
.end
        rts

blue_chain_stop_2p:
        tst.w       chain_timer_2p
        beq         .end
        bsr         blue_chain_end_2p
.end
        rts

; When a chain ends, record its final length.
; Count a single enemy as one hit; the game stores it separately until the second hit.
blue_chain_end_1p:
        move.w      sr,-(sp)
        movem.l     d0-d1/a0-a1,-(sp)
        move.w      stage_index,d0
        addq.w      #1,d0
        cmp.w       blue_chain_boss,d0
        beq         .end
        moveq       #0,d0
        move.w      chain_1p,d0
        bsr         blue_chain_number
        bne         .record
        tst.l       chain_first_1p
        beq         .end
        moveq       #1,d0
.record
        lea         blue_chain_1p,a0
        lea         blue_short_1p,a1
        bsr         blue_chain_record
.end
        movem.l     (sp)+,d0-d1/a0-a1
        move.w      (sp)+,ccr
        rts

blue_chain_end_2p:
        move.w      sr,-(sp)
        movem.l     d0-d1/a0-a1,-(sp)
        move.w      stage_index,d0
        addq.w      #1,d0
        cmp.w       blue_chain_boss,d0
        beq         .end
        moveq       #0,d0
        move.w      chain_2p,d0
        bsr         blue_chain_number
        bne         .record
        tst.l       chain_first_2p
        beq         .end
        moveq       #1,d0
.record
        lea         blue_chain_2p,a0
        lea         blue_short_2p,a1
        bsr         blue_chain_record
.end
        movem.l     (sp)+,d0-d1/a0-a1
        move.w      (sp)+,ccr
        rts

; Convert the game's packed-decimal HIT count in d0.w to an integer in d0.l.
; For example, $0200 becomes 200.
; Preserve other registers.
blue_chain_number:
        movem.l     d1-d3,-(sp)
        moveq       #0,d1
        moveq       #3,d2
.digit
        rol.w       #4,d0
        move.w      d0,d3
        andi.w      #$f,d3
        mulu.w      #10,d1
        add.w       d3,d1
        dbra        d2,.digit
        move.l      d1,d0
        movem.l     (sp)+,d1-d3
        rts

; Update the best chain and add lengths below CHAIN_THRESHOLD to BRK. d0.l = final length; a0 = best chain; a1 = 32-bit BRK sum.
blue_chain_record:
        cmp.w       (a0),d0
        bls         .short
        move.w      d0,(a0)
.short
        cmpi.w      #CHAIN_THRESHOLD,d0
        bcc         .end
        add.l       d0,(a1)
.end
        rts

; At Jetbachi's death, award stage 5's extend before Hibachi appears.
; A nonnegative life stock includes players waiting to respawn.
; Skip players with negative stock (game over or not joined).
; Clear tallies afterward so stage clear cannot award the same extend again.
blue_chain_extend_last:
        move.w      sr,-(sp)
        movem.l     d0-d7/a0-a6,-(sp)
        tst.w       ships_1p
        bmi         .p2
        bsr         blue_chain_extend_1p
.p2
        tst.w       ships_2p
        bmi         .end
        bsr         blue_chain_extend_2p
.end
        clr.w       blue_chain_1p
        clr.w       blue_chain_2p
        clr.l       blue_short_1p
        clr.l       blue_short_2p
        movem.l     (sp)+,d0-d7/a0-a6
        move.w      (sp)+,ccr
        rts

; After the normal stage-clear extend, award the chain extend if earned.
; Clear the player's tallies afterward, whether or not they earned a life.
blue_chain_extend_1p:
        movem.l     d0/a0-a1,-(sp)
        lea         blue_chain_1p,a0
        bsr         blue_chain_target_met
        bcs         .end
        lea         ships_1p,a1
        cmpi.w      #MAX_SHIPS,(a1)
        beq         .end
        addq.w      #1,(a1)
        jsr         sound_extend
        jsr         show_ships_1p
.end
        clr.l       blue_short_1p
        clr.w       (a0)
        movem.l     (sp)+,d0/a0-a1
        rts

blue_chain_extend_2p:
        movem.l     d0/a0-a1,-(sp)
        lea         blue_chain_2p,a0
        bsr         blue_chain_target_met
        bcs         .end
        lea         ships_2p,a1
        cmpi.w      #MAX_SHIPS,(a1)
        beq         .end
        addq.w      #1,(a1)
        jsr         sound_extend
        jsr         show_ships_2p
.end
        clr.l       blue_short_2p
        clr.w       (a0)
        movem.l     (sp)+,d0/a0-a1
        rts

; a0 = stage best; carry clear only when best > short-chain sum.
blue_chain_target_met:
        lea         blue_short_1p,a1
        cmpa.l      #blue_chain_1p,a0
        beq         .compare
        lea         blue_short_2p,a1
.compare
        moveq       #0,d0
        move.w      (a0),d0
        cmp.l       (a1),d0
        bls         .no
        andi        #$fffe,sr                   ; cc: met
        rts
.no
        ori         #1,sr                       ; cs: not met
        rts
