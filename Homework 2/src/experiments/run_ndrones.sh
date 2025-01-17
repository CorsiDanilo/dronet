#-----------------------------------------------------------#
#           _  _ ___  ___  ___  _  _ ___ ___                #
#          | \| |   \| _ \/ _ \| \| | __/ __|               #
#          | .` | |) |   / (_) | .` | _|\__ \               #
#          |_|\_|___/|_|_\\___/|_|\_|___|___/               #
#                                                           #
#-----------------------------------------------------------#


#test others algorithms
for nd in "5" "10" "15" "20" "25" "30";
do
    for alg in "QLS";
    do
        echo "run: ${alg} - ndrones ${nd} "
        python -m src.experiments.experiment_ndrones -nd ${nd} -i_s 5 -e_s 10 -alg ${alg} &
        python -m src.experiments.experiment_ndrones -nd ${nd} -i_s 10 -e_s 15 -alg ${alg} &
        python -m src.experiments.experiment_ndrones -nd ${nd} -i_s 15 -e_s 20 -alg ${alg} &
        python -m src.experiments.experiment_ndrones -nd ${nd} -i_s 20 -e_s 25 -alg ${alg} &
        python -m src.experiments.experiment_ndrones -nd ${nd} -i_s 25 -e_s 30 -alg ${alg} &
    done;
done;
wait


