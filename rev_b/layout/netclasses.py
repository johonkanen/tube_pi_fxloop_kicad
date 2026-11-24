"""Net classes of the PI + FX rev B (one list, read by tools/make_pcb.py and make_routing.py)."""

# Net classes by the DC voltage a net reaches (normal use, start-up, a short; raw rail 480 V transient).
HV = ["BP_RAW", "CS_PI", "CS_FX", "ZT_PI", "ZT_FX", "RF1_PI", "RF2_PI", "RF1_FX", "RF2_FX", "GF_PI", "GF_FX",
      "GP_PI", "GP_FX", "SRC_PI", "SRC_FX", "QB_PI", "QB_FX", "FBA_PI", "FBB_PI", "FBA_FX", "FBB_FX",
      "BPI", "BPI_P", "BFX", "BFX1", "BFX2", "DRV_A", "DRV_B"]          # 280-480 V
MV = ["Z1_PI", "Z2_PI", "Z1_FX", "BL1_PI", "BL2_PI", "BL1_FX", "BL2_FX", "PIR_M", "P1B"]   # 100-260 V
HEATER = ["HTR1", "HTR2"]
# High-impedance audio nodes (>= 47 kOhm or a grid): pours keep away, the opposite pour is cut under them.
HIZ = ["PRE_IN", "CI", "G1A", "SB", "RETURN_SIG", "RC", "NW", "DMX", "WMX", "M", "G1B", "ATT_IN", "ATT1", "ATT2", "ATT3",
       "ATT4", "ATT_OUT", "PIX", "G2A", "G2B", "G2BX", "FB_NODE", "PI_REF", "T_CL", "T_CR", "T_LD", "FN_CL", "FN_CR",
       "FN_LD", "FX_CL", "FX_CR", "FX_LD", "PRA_CL", "PRA_CR", "PRA_LD", "PRW_CL", "PRW_CR", "PRW_LD"]

# Routing groups (one KRT step each; KRT stamps obstacles at the largest clearance among one step's nets)
LOGIC = ["SPI_SCK", "SPI_MOSI", "SPI_MISO", "SPI_CS_N", "MUTE_ALL_N", "RESET_N", "FX_DRY", "FX_WET", "FX_UNMUTE",
         "FB_J_CL", "FB_J_CR", "FB_J_LD", "FB_RLY_CL", "FB_RLY_CR", "FB_RLY_LD", "ATT_1DB", "ATT_2DB", "ATT_4DB",
         "ATT_8DB", "ATT_16DB", "DRY_EN", "WET_EN"]
GATE = ["JDRV_DS", "JDRV_DH", "JDRV_WS", "JDRV_WH", "JDRV_FBS_CL", "JDRV_FBH_CL", "JDRV_FBS_CR", "JDRV_FBH_CR",
        "JDRV_FBS_LD", "JDRV_FBH_LD", "G_PAD", "GC_DS", "GC_WS", "GJ_DS", "GJ_DH", "GJ_WS", "GJ_WH",
        "GC_S1CL", "GC_S2CL", "GJ_S1CL", "GJ_S2CL", "GJ_HCL", "GC_S1CR", "GC_S2CR", "GJ_S1CR", "GJ_S2CR", "GJ_HCR",
        "GC_S1LD", "GC_S2LD", "GJ_S1LD", "GJ_S2LD", "GJ_HLD"]
COIL = ["RLY_ATT1_N", "RLY_ATT2_N", "RLY_ATT4_N", "RLY_ATT8_N", "RLY_ATT16_N", "RLY_FB_CL_N", "RLY_FB_CR_N", "RLY_FB_LD_N"]
AUDIO = ["K1A", "CFO", "SEND_SRC", "NP", "PD", "K1B", "KB", "ATP1", "ATP2", "ATP4", "ATP8", "ATP16", "PK", "PTOP", "QG",
         "QS", "SPK_CL", "SPK_CR", "SPK_LD", "FB_8R", "FB_RTN", "STP", "GND_DRV", "PAD_A"]
SUPPLY = ["+5V", "+15V", "-15V", "GNDD"]
