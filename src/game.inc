; Labels for in-game functions, memory addresses and constants.

; Where Blue Label's own code and work RAM go
BLUE_ROM              equ     $2c9100           ; free ROM after Version-B (to $2fffff)
BLUE_RAM              equ     $81e140           ; free work RAM after Version-B's (the stack starts at $820000 and grows down)

; Work RAM
game_loop             equ     $813098           ; .w 0: loop 1, 1: loop 2
stage_index           equ     $813092           ; .w stage 1-5 as 0-4
demo_playing          equ     $803926           ; .w not 0 while the attract demo plays
ship_state_1p         equ     $8103e6           ; .w negative while the ship is active
ship_state_2p         equ     $810448
ships_1p              equ     $8130be           ; .w spare ships; negative when not playing
ships_2p              equ     $8130c0
chain_1p              equ     $81b5da           ; .w packed decimal: the chain shown on screen now
chain_2p              equ     $81b604           ; .w packed decimal, 2P
chain_timer_1p        equ     $81b5c0           ; .w time left in the current chain
chain_timer_2p        equ     $81b5ea
chain_first_1p        equ     $81b5b8           ; .l first enemy of a chain, before its second hit
chain_first_2p        equ     $81b5e2
boss_flags            equ     $8130f8           ; .w bit 8 (bit 0 of the high byte): the stage's boss has appeared; cleared at each stage's start

; Routines
show_ships_1p         equ     $2878cc           ; redraw the spare-ship icons
show_ships_2p         equ     $28795c
sound_extend          equ     $28c678           ; the extend jingle
check_players         equ     $25fd94           ; end of a player's start: sorts out who is playing
ship_select_done      equ     $25db7c           ; ship select: the choice is complete

; Data
logo_palette          equ     $2259f8           ; label screen: logo (32 colours)
bee_palette           equ     $2259b8           ; label screen: the bee mark (32 colours)
label_bg_palette      equ     $23046c           ; label screen: background (32 colours)

; Numbers
MAX_SHIPS             equ     20                ; most spare ships
SHIP_SHOT_POWER       equ     $20               ; .w weapon levels are stored as 0,2,4,6,8
SHIP_LASER_POWER      equ     $22

; Player selection data (a6) and its fields
SEL_STEP              equ     1                 ; .b which step of the choice
SEL_DOLL              equ     4                 ; .w the chosen element doll
STEP_SHIP             equ     1                 ; choosing the ship
STEP_DOLL_DONE        equ     5                 ; the doll choice has ended
STEP_LAUNCH           equ     7                 ; waiting to launch
DOLL_EXY              equ     2                 ; Exy (expert)

; the player's task (a5) during ship select
TASK_DOLL_1P          equ     6                 ; .b the doll the game will use, 1P
TASK_DOLL_2P          equ     7                 ; .b and 2P

; Ship-select screen data (a5) for its last steps
SHIPSEL_DOLL          equ     $f                ; .b the doll chosen
SHIPSEL_TABLE         equ     8                 ; .l this player's table
SHIPSEL_TAG           equ     16                ; .l in the table: the player's task
TAG_DOLL              equ     1                 ; .b in that task: the doll

; HUD: native movement data and sprite submission
hud_entering          equ     $81b6ee           ; .w start-of-stage panel entrance
hud_motion            equ     $81b620           ; .w shared entrance/exit counter
hud_phase             equ     $81b61e           ; .w boss-bar/panel transition steps
stage_clear_flags     equ     $81df1e           ; .w bit 3: stage-clear transition
hud_sprite_bytes      equ     $80afe6           ; .w bytes used in the HUD sprite queue
submit_hud_sprite     equ     $23fa96           ; d1: fixed-point coordinates, d2: picture, d3: size, d4: palette; breaks d0/a0

; Native spare-ship movement and selected hulls
life_slide_y          equ     $81b622
life_slide_x          equ     $81b624
hull_type_1p          equ     $813084
hull_type_2p          equ     $813086

; Full-power setup also selects the native shot and option firing-rate tables
fill_power_1p         equ     $252dac
fill_power_2p         equ     $252e26
