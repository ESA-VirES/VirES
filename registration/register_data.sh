#!/bin/sh -e
#
# Register Swarm data in your local Vagrant environment
#
# Note: To be executed with the right permissions!
#
cd "`dirname "$0"`"
#MNG="sudo -u vires python ${VIRES_INSTANCE_DIR:-/var/www/vires/eoxs}/manage.py"
MNG="../scripts/venv_eoxs_manage"
DATA_DIR="${DATA_DIR:-/mnt/data}"
chmod 0755 ~/

$MNG product_type import
$MNG product_collection import

[ -f "$PWD/Dst_MJD_1998.dat" ] || wget 'ftp://ftp.gfz-potsdam.de/pub/incoming/champ_payload/Nils/Dst_MJD_1998.dat' -O "$PWD/Dst_MJD_1998.dat"
[ -f "$PWD/Kp_MJD_1998_QL.dat" ] || wget 'ftp://ftp.gfz-potsdam.de/pub/incoming/champ_payload/Nils/Kp_MJD_1998_QL.dat' -O "$PWD/Kp_MJD_1998_QL.dat"

$MNG cached_product update GFZ_AUX_DST "$PWD/Dst_MJD_1998.dat"
$MNG cached_product update GFZ_AUX_KP "$PWD/Kp_MJD_1998_QL.dat"

$MNG cached_product update AUX_F10_2_ /mnt/data/SWARM/AUX_F10_2_/SW_OPER_AUX_F10_2__*.DBL

# models

# MCO
$MNG cached_product update MCO_SHA_2C /mnt/data/SWARM/MCO_SHA/SW_OPER_MCO_SHA_2C_*.shc
$MNG cached_product update MCO_SHA_2D /mnt/data/SWARM/MCO_SHA/SW_OPER_MCO_SHA_2D_*.shc
$MNG cached_product update MCO_SHA_2F /mnt/data/SWARM/MCO_SHA/SW_OPER_MCO_SHA_2F_*.shc
$MNG cached_product update MCO_SHA_2X /mnt/data/SWARM/MCO_SHA/SW_OPER_MCO_SHA_2X_*.shc

# MLI
$MNG cached_product update MLI_SHA_2C /mnt/data/SWARM/MLI_SHA/SW_OPER_MLI_SHA_2C_*.shc
$MNG cached_product update MLI_SHA_2D /mnt/data/SWARM/MLI_SHA/SW_OPER_MLI_SHA_2D_*.shc

# MMA
$MNG cached_product update MMA_SHA_2F /mnt/data/SWARM/MMA_SHA/2F/*.cdf
$MNG cached_product update MMA_SHA_2C /mnt/data/SWARM/MMA_SHA/2C/*.cdf
$MNG cached_product update MMA_CHAOS_ /mnt/data/SWARM/MMA_SHA/CHAOS6/*.cdf

# MIO
$MNG cached_product update MIO_SHA_2C /mnt/data/SWARM/MIO_SHA/SW_OPER_MIO_SHA_2C_*.txt
$MNG cached_product update MIO_SHA_2D /mnt/data/SWARM/MIO_SHA/SW_OPER_MIO_SHA_2D_*.txt

# load orbit counters
for SAT in A B C
do
    find "$DATA_DIR" -type f -name "SW_OPER_AUX${SAT}ORBCNT_*.TXT" | tail -n 1 | while read FILE
    do
        $MNG cached_product update "AUX${SAT}ORBCNT" "$FILE"
    done
done

COLLECTION="SW_OPER_AUX_IMF_2_"
find "$DATA_DIR" -type f -name "SW_OPER_AUX_IMF_2_*.DBL" | sort \
| $MNG product register -c "$COLLECTION" -f - --conflict=UPDATE

for SAT in A B C
do
    COLLECTION="SW_OPER_MAG${SAT}_HR_1B"
    find "$DATA_DIR" -type f -name "SW_OPER_MAG${SAT}*MDR_MAG_HR.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --conflict=UPDATE
done

# re-build orbit direction lookup tables
#$MNG orbit_directions rebuild

for SAT in A B C
do
    COLLECTION="SW_OPER_MAG${SAT}_LR_1B"
    # product registration including update of the orbit direction lookup tables
    find "$DATA_DIR" -type f -name "SW_OPER_MAG${SAT}*MDR_MAG_LR.cdf" | sort \
    | $MNG product --traceback register -c "$COLLECTION" -f - --conflict=UPDATE
done

for SAT in A B C
do
    COLLECTION="SW_OPER_EFI${SAT}_LP_1B"
    [ -f "./ERROR" ] && break
    find "$DATA_DIR" -type f -name "SW_OPER_EFI${SAT}*MDR_EFI_LP.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --conflict=UPDATE
done

for SAT in A B C
do
    COLLECTION="SW_OPER_IBI${SAT}TMS_2F"
    find "$DATA_DIR" -type f -name "SW_OPER_IBI${SAT}TMS_2F*.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --conflict=UPDATE --overlap=IGNORE
done

for SAT in A B C
do
    COLLECTION="SW_OPER_TEC${SAT}TMS_2F"
    [ -f "./ERROR" ] && break
    find "$DATA_DIR" -type f -name "${COLLECTION}_*.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --conflict=UPDATE
done

for SAT in _ A B C
do
    COLLECTION="SW_OPER_FAC${SAT}TMS_2F"
    [ -f "./ERROR" ] && break
    find "$DATA_DIR" -type f -name "${COLLECTION}_*.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --conflict=UPDATE
done

for SAT in A B
do
    COLLECTION="SW_OPER_EEF${SAT}TMS_2F"
    find "$DATA_DIR" -type f -name "SW_OPER_EEF${SAT}TMS_2F*.DBL" | sort \
    | $MNG product register -c "$COLLECTION" -f - --conflict=UPDATE --overlap=IGNORE
done

for SAT in A B C
do
    COLLECTION="SW_OPER_IPD${SAT}IRR_2F"
    find "$DATA_DIR" -type f -name "SW_OPER_IPD${SAT}IRR_2F*.cdf" | sort \
    | $MNG product register -c "$COLLECTION" -f - --conflict=UPDATE
done

#for SAT in A B C
#do
#    COLLECTION="SW_OPER_AEJ${SAT}LPL_2F"
#    $MNG product deregister -c "$COLLECTION" --all
#    set -x
#    find "$DATA_DIR" -type f -name "SW_OPER_AEJ${SAT}LPL_2F_20*.cdf" | sort \
#    | $MNG product register -c "$COLLECTION" -f - --conflict=UPDATE
#done

#for SAT in A B C
#do
#    COLLECTION="SW_OPER_AEJ${SAT}PBL_2F"
#    $MNG product deregister -c "$COLLECTION" --all
#    set -x
#    find "$DATA_DIR" -type f -name "SW_OPER_AEJ${SAT}PBL_2F_20*.cdf" | sort \
#    | $MNG product register -c "$COLLECTION" -f - --conflict=UPDATE
#done

#for SAT in A B C
#do
#    COLLECTION="SW_OPER_AEJ${SAT}LPS_2F"
#    $MNG product deregister -c "$COLLECTION" --all
#    set -x
#    find "$DATA_DIR" -type f -name "SW_OPER_AEJ${SAT}LPS_2F_20*.cdf" | sort \
#    | $MNG product register -c "$COLLECTION" -f - --conflict=UPDATE
#done

#for SAT in A B C
#do
#    COLLECTION="SW_OPER_AEJ${SAT}PBS_2F"
#    $MNG product deregister -c "$COLLECTION" --all
#    set -x
#    find "$DATA_DIR" -type f -name "SW_OPER_AEJ${SAT}PBS_2F_20*.cdf" | sort \
#    | $MNG product register -c "$COLLECTION" -f - --conflict=UPDATE
#done

#for SAT in A B C
#do
#    COLLECTION="SW_OPER_AEJ${SAT}PBS_2F:PGMFD"
#    $MNG product deregister -c "$COLLECTION" --all
#    set -x
#    find "$DATA_DIR" -type f -name "SW_OPER_AEJ${SAT}PBS_2F_20*.cdf" | sort \
#    | $MNG product register -c "$COLLECTION" -f - --conflict=UPDATE
#done

#for SAT in A B C
#do
#    COLLECTION="SW_OPER_AOB${SAT}FAC_2F"
#    $MNG product deregister -c "$COLLECTION" --all
#    set -x
#    find "$DATA_DIR" -type f -name "SW_OPER_AOB${SAT}FAC_2F_20*.cdf" | sort \
#    | $MNG product register -c "$COLLECTION" -f - --conflict=UPDATE
#done