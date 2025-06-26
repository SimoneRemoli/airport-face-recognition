from pathlib import Path

from sim.welford import estimate
from sim.executor import SchedulingPolicy
from simio.simprint import sprint

def print_verify_output(exp, pc_values):

    keys=[
        "E_rho",
        "E_Si",
        "E_Tq",
        "E_Ts",
        "E_Nq",
        "E_Ns",
        "C_S",
        "C_Ns",
        "pc"
          ]
    stats=exp.results
    DIR = "OUTPUT/" + exp.description
    Path(DIR).mkdir(parents=True, exist_ok=True)
    header=""
    for pc in pc_values:
        expected_values={k:None for k in keys}
        expected_values["pc"]=pc
        if exp.scheduling_policies[0] is SchedulingPolicy.PS:
            header="SINGLE-SERVER"
            if pc==0:
                expected_values["E_rho"]=0.7
                expected_values["E_Si"]=0.5
                expected_values["E_Tq"]=1.16
                expected_values["E_Ts"]=1.66
                expected_values["E_Nq"]=1.624
                expected_values["E_Ns"]=2.33333
                expected_values["C_S"]=0
                expected_values["C_Ns"]=0
            if pc==0.4:
                expected_values["E_rho"]=0.75599
                expected_values["E_Si"]=0.38571
                expected_values["E_Tq"]=1.195
                expected_values["E_Ts"]=1.58071
                expected_values["E_Nq"]=2.3422
                expected_values["E_Ns"]=3.09819
                expected_values["C_S"]=0.8
                expected_values["C_Ns"]=0.448
        elif exp.scheduling_policies[0] is SchedulingPolicy.FIFO:
            header="MULTISERVER"
            if pc==0:
                expected_values["E_rho"]=0.35
                expected_values["E_Si"]=0.5
                expected_values["E_Tq"]=0.0698
                expected_values["E_Ts"]=0.5698
                expected_values["E_Nq"]=0.09772
                expected_values["E_Ns"]=0.79772
                expected_values["C_S"]=0
                expected_values["C_Ns"]=0
            if pc==0.4:
                expected_values["E_rho"]=0.378
                expected_values["E_Si"]=0.38571
                expected_values["E_Tq"]=0.07858
                expected_values["E_Ts"]=0.46429
                expected_values["E_Nq"]=0.15402
                expected_values["E_Ns"]=0.91001
                expected_values["C_S"]=0.8
                expected_values["C_Ns"]=0.448

        filename = DIR+'/VERIFY-human_readable-pc' + str(pc)
        with open(filename, 'w') as f:
            sprint(f"----------------------")
            sprint(f"{header}: Verify results for pc = {pc}:")
            avgs = {key: [] for key in keys}
            for k, v in stats.items():
                if k.pc == pc:
                    for k in keys:
                        avgs[k].append(v[k])

            sprint("name\texpected\tresult\t\t\t\tverified")
            print("name\texpected\tresult\t\t\t\tverified", file=f)

            for k in keys:
                avg, _, w = estimate(avgs[k])
                sprint(k, "\t", expected_values[k],"\t", avg, "\t+/-\t", w, avg-w<=expected_values[k]<=avg+w)
                print(k, "\t", expected_values[k], "\t", avg, "\t+/-\t", w, avg-w<=expected_values[k]<=avg+w, file=f)
