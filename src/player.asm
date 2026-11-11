; Before player setup, select loop 1 so the game initializes lives and extends normally.
; Clear both players' chain tallies for the new game. blue_player_started switches to loop 2 after setup.
blue_player_start:
        clr.w       game_loop
        bsr         blue_chain_clear
        rts

; Finish player setup, then select loop 2.
; Keep attract demos on loop 1 so their recorded inputs still match.
blue_player_started:
        jsr         check_players
        tst.w       demo_playing
        bne         .demo
        move.w      #1,game_loop
.demo
        rts

; On ship creation, fill weapon power without changing bomb stock or capacity. a6 points to the ship's runtime data.
; Leave attract demos unchanged.
blue_new_ship:
        tst.w       demo_playing
        bne         .demo
        bsr         blue_full_power
.demo
        rts

; a6 points to the new ship.
; Use the game's maximum-power routine to set both weapon levels and their matching shot/option firing-rate tables.
blue_full_power:
        move.w      sr,-(sp)
        movem.l     d0-d7/a0-a6,-(sp)
        cmpa.l      #ship_state_1p,a6
        bne         .p2
        jsr         fill_power_1p
        bra         .end
.p2
        jsr         fill_power_2p
.end
        movem.l     (sp)+,d0-d7/a0-a6
        move.w      (sp)+,ccr
        rts

; After ship selection, assign Exy and finish selection without opening the doll menu.
blue_ship_chosen:
        move.b      #DOLL_EXY,SHIPSEL_DOLL(a5)
        movea.l     SHIPSEL_TABLE(a5),a4
        movea.l     SHIPSEL_TAG(a4),a0
        move.b      SHIPSEL_DOLL(a5),TAG_DOLL(a0)
        jmp         ship_select_done

; If doll selection is entered, assign Exy and mark selection complete. a6 points to selection data; a5 points to the player task. d7 is nonzero for 1P and zero for 2P.
blue_doll_choice:
        move.w      #DOLL_EXY,SEL_DOLL(a6)
        tst.w       d7
        beq         .p2
        move.b      SEL_DOLL+1(a6),TASK_DOLL_1P(a5)
        bra         .set
.p2
        move.b      SEL_DOLL+1(a6),TASK_DOLL_2P(a5)
.set
        move.b      #STEP_DOLL_DONE,SEL_STEP(a6)
        rts

; Keep the ship card visible through the launch wait so it can slide away in place of the skipped doll card. a6 points to selection data.
; Return Z set when the card should be drawn.
blue_ship_card_shown:
        cmpi.b      #STEP_SHIP,SEL_STEP(a6)
        bcs         .no
        cmpi.b      #STEP_LAUNCH,SEL_STEP(a6)
        bhi         .no
        move        #4,ccr                      ; Z: draw
        rts
.no
        move        #0,ccr
        rts

; Add the launch slide offset (d6) to the ship card's Y position (d1).
blue_ship_card_slide:
        add.w       d6,d1
        rts
