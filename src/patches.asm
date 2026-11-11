; Fixed-address edits and hooks, grouped by feature.
;
; HOOK before|after, ADDRESS, LENGTH, ROUTINE replaces complete instructions with a jump to a trampoline.
; Original instructions are copied directly from the provided ROM.
; LENGTH is even and >= 6; instructions must be safe to relocate (no PC-relative operands or relative branches).
;
; org writes a fixed-size replacement.
; BUILD_DATE inserts the beta date line.
;

; At the version menu, select Version-B and jump to its normal launch path.
        org         $13beea
        move.w      #1,$81585c                  ; the menu's choice: 1 = Version-B
        bra.w       $13c0ba                     ; start the chosen version

; Skip Version-B's one-round/two-round menu during launch.
        org         $25d57e
        nop
        nop
        nop

; Before player setup, use normal loop-1 initialization and clear chain tallies.
        HOOK        before, $2601f4, 10, blue_player_start

; Replace the final player-setup call with a wrapper that selects loop 2.
        org         $2602b0
        jmp         blue_player_started

; Allow normal paid continues in stage 5.
; Keep the game's continue settings.
        org         $288a96
        nop
        nop

; Remove the stage-5 restriction from coin/start handling and INSERT COIN.
        org         $25dbe8
        nop
        nop
        org         $25dc4c
        nop
        nop
        org         $260af0
        nop

; Fill weapon power during ship setup, before the bomb display is initialized.
        HOOK        before, $249388, 6, blue_new_ship

; After ship selection on continue or join-in, assign Exy and skip the doll menu.
        org         $25dcdc
        jmp         blue_ship_chosen

; If doll selection is entered, complete it immediately with Exy.
        org         $25d394
        jmp         blue_doll_choice

; Extend ship-card visibility through the launch wait.
        org         $25e846
        jsr         blue_ship_card_shown
        bne.w       $25e99e

; Move both ships' cards and logos with the launch slide.
        HOOK        after, $25e89c, 8, blue_ship_card_slide
        HOOK        after, $25e8be, 8, blue_ship_card_slide
        HOOK        after, $25e942, 8, blue_ship_card_slide
        HOOK        after, $25e966, 8, blue_ship_card_slide

; Hide the three doll cards, as in the game's loop 2.
        org         $25ea00
        bra.w       $25ea30
        org         $25ea7e
        bra.w       $25eaae
        org         $25eafc
        bra.w       $25eb2c

; Update stage-best chains each frame after the continue display.
        HOOK        after, $2607f0, 6, blue_chain_frame

; Record expired chains before the game clears their data.
        HOOK        before, $28463e, 8, blue_chain_end_1p
        HOOK        before, $2847dc, 8, blue_chain_end_2p

; Record chains ended by bombs, the post-bomb delay or respawning.
        HOOK        before, $2877d0, 8, blue_chain_stop_1p
        HOOK        before, $2877fe, 8, blue_chain_stop_2p
        HOOK        before, $28782c, 8, blue_chain_stop_1p
        HOOK        before, $287842, 8, blue_chain_stop_2p
        HOOK        before, $253a1e, 10, blue_chain_stop_1p
        HOOK        before, $253a3a, 10, blue_chain_stop_2p

; Freeze each stage's chain tallies when its boss appears.
        HOOK        before, $2926da, 6, blue_chain_boss_start
        HOOK        before, $297118, 6, blue_chain_boss_start
        HOOK        before, $29bbf4, 6, blue_chain_boss_start
        HOOK        before, $29ec7a, 6, blue_chain_boss_start

; Freeze stage 5's tallies at Koryu's entrance, before the boss sequence.
        HOOK        before, $2a42d4, 6, blue_chain_boss_last

; Award stage 5's chain extend when Jetbachi's death explosion starts.
        HOOK        before, $2a5f8e, 12, blue_chain_extend_last

; Check both players' chain extends after the normal loop-2 stage extend.
        HOOK        before, $25314a, 6, blue_chain_extend_1p
        HOOK        before, $25319a, 6, blue_chain_extend_2p

; Generate the blue palettes at both startup-screen entry points.
        HOOK        before, $25bd7c, 12, blue_label_palettes
        HOOK        before, $25bde0, 10, blue_label_palettes

; Use the blue palettes for normal display and fade-in.
        org         $25bdf6
        dc.l        blue_bg_pal
        org         $25be74
        dc.l        blue_logo_pal
        org         $25be84
        dc.l        blue_bee_pal
        org         $25bfc2
        dc.l        blue_logo_pal
        org         $25bfd0
        dc.l        blue_bee_pal
        org         $25c008
        dc.l        blue_bg_pal

; Boot screen: the version line

        org         $25abd6
        BUILD_DATE                              ; build.py inserts today and the BETA version line

; Submit BRK and life counts after the native HUD advances its movement.
; Use the same sprite queue so both displays update on the same video frame.
        HOOK        after, $28d534, 6, blue_hud_frame

; Native spare-ship display: one icon, followed by our xN count.
; Only display-loop bounds change; gameplay stock remains untouched.
        org         $284d5a
        dc.w        0
        org         $284d5e
        moveq       #0,d0
        org         $284df4
        dc.w        0
        org         $284df8
        moveq       #0,d0
        org         $284e8c
        dc.w        0
        org         $284e90
        moveq       #0,d7
        org         $284f04
        dc.w        0
        org         $284f08
        moveq       #0,d7
        org         $28501c
        dc.w        0
        org         $285020
        moveq       #0,d0
        org         $2850f8
        dc.w        0
        org         $2850fc
        moveq       #0,d0
        org         $285220
        dc.w        0
        org         $285224
        moveq       #0,d0
        org         $2852fa
        dc.w        0
        org         $2852fe
        moveq       #0,d0
        org         $28791a
        dc.w        0
        org         $28791e
        moveq       #0,d6
        org         $2879a4
        dc.w        0
        org         $2879a8
        moveq       #0,d6
