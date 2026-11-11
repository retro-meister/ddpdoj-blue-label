; Work RAM (BLUE_RAM)
        rsset BLUE_RAM
blue_chain_1p         rs.w    1                 ; .w 1P's best chain in this stage, before its boss
blue_chain_2p         rs.w    1                 ; .w 2P's
blue_logo_pal         rs.w    32                ; 32 colours: the logo's palette, blue
blue_bee_pal          rs.w    32                ; the bee mark's
blue_bg_pal           rs.w    32                ; the background's
blue_pal_done         rs.w    1                 ; .w BLUE_DONE once the three are made
blue_chain_boss       rs.w    1                 ; .w stage whose boss has appeared (1-5)
blue_short_1p         rs.l    1                 ; .l sum of completed chains below CHAIN_THRESHOLD
blue_short_2p         rs.l    1
blue_hud_stage        rs.w    1                 ; .w stage whose result is being displayed
blue_hud_best_1       rs.w    1                 ; .w stage bests, displayed until the next stage
blue_hud_best_2       rs.w    1
blue_hud_short_1      rs.l    1                 ; .l short-chain sums, displayed until the next stage
blue_hud_short_2      rs.l    1
blue_hud_flash_1      rs.w    1                 ; .w brief digit pulse when the sum increases
blue_hud_flash_2      rs.w    1
BLUE_RAM_END          rs.b    0

BLUE_DONE             equ     $b1e5
