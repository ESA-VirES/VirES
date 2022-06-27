#!/bin/sh -e
#
# Register Swarm data in your local Vagrant environment
#
# Note: To be executed with the right permissions!
#
cd "`dirname "$0"`"
#MNG="sudo -u vires python ${VIRES_INSTANCE_DIR:-/var/www/vires/eoxs}/manage.py"
MNG="../scripts/venv_vires_manage"
DATA_DIR="${DATA_DIR:-/mnt/data}"
chmod 0755 ~/

$MNG product_type import --default
$MNG product_collection import --default
$MNG product deregister --invalid

[ -f "$PWD/Dst_MJD_1998.dat" ] || wget 'ftp://ftp.gfz-potsdam.de/pub/incoming/champ_payload/Nils/Dst_MJD_1998.dat' -O "$PWD/Dst_MJD_1998.dat"
[ -f "$PWD/Kp_MJD_1998_QL.dat" ] || wget 'ftp://ftp.gfz-potsdam.de/pub/incoming/champ_payload/Nils/Kp_MJD_1998_QL.dat' -O "$PWD/Kp_MJD_1998_QL.dat"

$MNG cached_product update GFZ_AUX_DST "$PWD/Dst_MJD_1998.dat"
$MNG cached_product update GFZ_AUX_KP "$PWD/Kp_MJD_1998_QL.dat"

$MNG cached_product update AUX_F10_2_ `find $DATA_DIR -name SW_OPER_AUX_F10_2__\*.DBL | sort | tail -n 1`

# models

# MCO
$MNG cached_product update MCO_SHA_2C `find $DATA_DIR -name SW_OPER_MCO_SHA_2C_\*.shc | sort | tail -n 1`
$MNG cached_product update MCO_SHA_2D `find $DATA_DIR -name SW_OPER_MCO_SHA_2D_\*.shc | sort | tail -n 1`
$MNG cached_product update MCO_SHA_2F `find $DATA_DIR -name SW_OPER_MCO_SHA_2F_\*.shc | sort | tail -n 1`
$MNG cached_product update MCO_SHA_2X `find $DATA_DIR -name SW_OPER_MCO_SHA_2X_\*.shc | sort | tail -n 1`

# MLI
$MNG cached_product update MLI_SHA_2C `find $DATA_DIR -name SW_OPER_MLI_SHA_2C_\*.shc | sort | tail -n 1`
$MNG cached_product update MLI_SHA_2D `find $DATA_DIR -name SW_OPER_MLI_SHA_2D_\*.shc | sort | tail -n 1`
$MNG cached_product update MLI_SHA_2E `find $DATA_DIR -name SW_OPER_MLI_SHA_2D_\*.shc | sort | tail -n 1`

# MMA
$MNG cached_product update MMA_SHA_2F `find $DATA_DIR -name SW_OPER_MMA_SHA_2F_\*.cdf`
$MNG cached_product update MMA_SHA_2C `find $DATA_DIR -name SW_OPER_MMA_SHA_2C_\*.cdf`
$MNG cached_product update MMA_CHAOS_ `find $DATA_DIR -name SW_OPER_MMA_CHAOS__\*.cdf`

# MIO
$MNG cached_product update MIO_SHA_2C `find $DATA_DIR -name SW_OPER_MIO_SHA_2C_\*.txt | sort | tail -n 1`
$MNG cached_product update MIO_SHA_2D `find $DATA_DIR -name SW_OPER_MIO_SHA_2D_\*.txt | sort | tail -n 1`

# load orbit counters

# Swarm orbit counters
for SAT in A B C
do
    find "$DATA_DIR" -type f -name "SW_OPER_AUX${SAT}ORBCNT_*.TXT" | tail -n 1 | while read FILE
    do
        $MNG cached_product update "AUX${SAT}ORBCNT" "$FILE"
    done
done

# CryoSat-2 orbit counters
find "$DATA_DIR" -type f -name "CS_OPER_AUX_ORBCNT_*.TXT" | tail -n 1 | while read FILE
do
    $MNG cached_product update "CS2_ORBCNT" "$FILE"
done

# GRACE orbit counters
for SAT in 1 2
do
    find "$DATA_DIR" -type f -name "GR${SAT}_ORBCNT_*.cdf" | tail -n 1 | while read FILE
    do
        $MNG cached_product update "GR${SAT}_ORBCNT" "$FILE"
    done
done

# GRACE-FO orbit counters
for SAT in 1 2
do
    find "$DATA_DIR" -type f -name "GF${SAT}_ORBCNT_*.cdf" | tail -n 1 | while read FILE
    do
        $MNG cached_product update "GF${SAT}_ORBCNT" "$FILE"
    done
done

# GOCE orbit counters
find "$DATA_DIR" -type f -name "GO_ORBCNT_*.cdf" | tail -n 1 | while read FILE
do
    $MNG cached_product update "GO_ORBCNT" "$FILE"
done

# OMNI datasets
COLLECTION="OMNI_HR_1min_avg20min_delay10min"
find "$DATA_DIR" -type f -name "omni_hro_1min_*_avg20min_delay10min.cdf" | sort \
| $MNG product register -c "$COLLECTION" -f - --update

COLLECTION="OMNI_HR_1min"
find "$DATA_DIR" -type f -name "omni_hro_1min_*_v[0-9][0-9].cdf" | sort \
| $MNG product register -c "$COLLECTION" -f - --update

COLLECTION="SW_OPER_AUX_IMF_2_"
find "$DATA_DIR" -type f -name "SW_OPER_AUX_IMF_2_*.DBL" | sort \
| $MNG product register -c "$COLLECTION" -f - --update

# re-build orbit direction lookup tables
#$MNG orbit_directions rebuild

# Swarm products ...
for SAT in A B C
do
    COLLECTION="SW_OPER_MOD${SAT}_SC_1B"
    # product registration including update of the orbit direction lookup tables
    find "$DATA_DIR" -type f -name "${COLLECTION}_*\.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
done

for SAT in A B C
do
    COLLECTION="SW_OPER_MAG${SAT}_LR_1B"
    find "$DATA_DIR" -type f -name "SW_OPER_MAG${SAT}*MDR_MAG_LR.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
done

for SAT in A B C
do
    COLLECTION="SW_OPER_MAG${SAT}_HR_1B"
    find "$DATA_DIR" -type f -name "SW_OPER_MAG${SAT}*MDR_MAG_HR.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
done

for SAT in A B C
do
    COLLECTION="SW_OPER_EFI${SAT}_LP_1B"
    [ -f "./ERROR" ] && break
    find "$DATA_DIR" -type f -name "SW_OPER_EFI${SAT}*MDR_EFI_LP.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
done

for SAT in A B C
do
    COLLECTION="SW_OPER_EFI${SAT}TIE_2_"
    find "$DATA_DIR" -type f -name "${COLLECTION}_*.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
done

for SAT in A B C
do
    COLLECTION="SW_EXPT_EFI${SAT}_TCT02"
    find "$DATA_DIR" -type f -name "${COLLECTION}_*.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
done

for SAT in A B C
do
    COLLECTION="SW_EXPT_EFI${SAT}_TCT16"
    find "$DATA_DIR" -type f -name "${COLLECTION}_*.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
done

for SAT in A B C
do
    COLLECTION="SW_OPER_IBI${SAT}TMS_2F"
    find "$DATA_DIR" -type f -name "SW_OPER_IBI${SAT}TMS_2F*.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
done

for SAT in A B C
do
    COLLECTION="SW_OPER_TEC${SAT}TMS_2F"
    find "$DATA_DIR" -type f -name "${COLLECTION}_*.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
done

for SAT in _ A B C
do
    COLLECTION="SW_OPER_FAC${SAT}TMS_2F"
    find "$DATA_DIR" -type f -name "${COLLECTION}_*.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
done

for SAT in A B C
do
    COLLECTION="SW_OPER_EEF${SAT}TMS_2F"
    find "$DATA_DIR" -type f -name "SW_OPER_EEF${SAT}TMS_2F*_0[2-9][0-9][1-9].cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
done

for SAT in A B C
do
    COLLECTION="SW_OPER_IPD${SAT}IRR_2F"
    find "$DATA_DIR" -type f -name "SW_OPER_IPD${SAT}IRR_2F*.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
done

for SAT in A B C
do
    COLLECTION="SW_OPER_AEJ${SAT}LPL_2F"
    find "$DATA_DIR" -type f -name "SW_OPER_AEJ${SAT}LPL_2F_20*.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
done

for SAT in A B C
do
    COLLECTION="SW_OPER_AEJ${SAT}LPL_2F"
    find "$DATA_DIR" -type f -name "SW_OPER_AEJ${SAT}LPL_2F_20*.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
done

for SAT in A B C
do
    COLLECTION="SW_OPER_AEJ${SAT}PBL_2F"
    find "$DATA_DIR" -type f -name "SW_OPER_AEJ${SAT}PBL_2F_20*.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
done

for SAT in A B C
do
    COLLECTION="SW_OPER_AEJ${SAT}LPS_2F"
    find "$DATA_DIR" -type f -name "SW_OPER_AEJ${SAT}LPS_2F_20*.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
done

for SAT in A B C
do
    COLLECTION="SW_OPER_AEJ${SAT}PBS_2F"
    find "$DATA_DIR" -type f -name "SW_OPER_AEJ${SAT}PBS_2F_20*.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
done

for SAT in A B C
do
    COLLECTION="SW_OPER_AOB${SAT}FAC_2F"
    find "$DATA_DIR" -type f -name "SW_OPER_AOB${SAT}FAC_2F_20*.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
done

for SAT in A B C
do
    COLLECTION="SW_OPER_MIT${SAT}_LP_2F"
    find "$DATA_DIR" -type f -name "${COLLECTION}_*\.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
done

for SAT in A B C
do
    COLLECTION="SW_OPER_MIT${SAT}TEC_2F"
    find "$DATA_DIR" -type f -name "${COLLECTION}_*\.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
done

for SAT in A B C
do
    COLLECTION="SW_OPER_PPI${SAT}FAC_2F"
    find "$DATA_DIR" -type f -name "${COLLECTION}_*\.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
done

# VOBS Swarm
for TYPE in 1M 4M
do
    COLLECTION="SW_OPER_VOBS_${TYPE}_2_"
    find "$DATA_DIR" -type f -name "${COLLECTION}*\.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
done

# VOBS non-Swarm
TYPE=4M
for MISSION in CH CO CR OR
do
    COLLECTION="${MISSION}_OPER_VOBS_${TYPE}_2_"
    find "$DATA_DIR" -type f -name "${COLLECTION}*\.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
done

# Ground observatory data
for TYPE in S M
do
    COLLECTION="SW_OPER_AUX_OBS${TYPE}2_"
    find "$DATA_DIR" -type f -name "SW_OPER_AUX_OBS${TYPE}2_*.DBL" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
done

COLLECTION="SW_OPER_AUX_OBSH2_"
find "$DATA_DIR" -type f -name "SW_OPER_AUX_OBS_2_*.cdf" | sort \
| $MNG product register -c "$COLLECTION" -f - --update


# GRACE magnetic products
for SAT in A B
do
    set -x
    COLLECTION="GRACE_${SAT}_MAG"
    find "$DATA_DIR" -type f -name "${COLLECTION}_*.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
    set +x
done

# GRACE-FO magnetic products
for SAT in 1 2
do
    COLLECTION="GF${SAT}_OPER_FGM_ACAL_CORR"
    find "$DATA_DIR" -type f -name "${COLLECTION}_*.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --update
done

# CryoSat-2 magnetic products
COLLECTION="CS_OPER_MAG"
find "$DATA_DIR" -type f -name "CS_OPER_MAG_*.cdf" | sort \
| $MNG product register -c "$COLLECTION" -f - --update

# GOCE magnetic products
COLLECTION="GO_MAG_ACAL_CORR"
find "$DATA_DIR" -type f -name "GO_MAG_ACAL_CORR*.cdf" | sort \
| $MNG product register -c "$COLLECTION" -f - --update
