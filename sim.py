# encoding=utf8
__author__ = 'Majid Khonji'

import numpy as np
import time, pickle
import util as u
import instance as ii
import s_maxOPF_algs as ss
import OPF_algs as oo
import logging


# sim for EV-scheduling (E-Energy 2018 and SmartGridComm 2018) #PTAS
def sim_ev_fixed_interval(scenario="L", max_n=1000, step_n=50, start_n=100, reps=40, capacity=1000000, dry_run=False,
                          dump_dir="results/dump/"):
    name = "EV2[%s]__fixed_int_max_n=%d_step_n=%d_start_n=%d_reps=%d_capacity=%d" % (
        scenario, max_n, step_n, start_n, reps, capacity)
    ### set up variables
    assert (max_n % step_n == 0)
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)

    t1 = time.time()
    #####

    round_EV_obj = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    round_EV_time = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    round_EV_ar = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    round_EV_frac_x_count = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    round_EV_frac_com_percentage = np.zeros(((max_n - start_n + step_n) / step_n, reps))

    frac_OPT_EV_obj = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    frac_OPT_EV_time = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    frac_OPT_EV_num_of_constraints = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    solution_x_k = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    failure_count = {}
    failure_OPT_count = {}

    for n in range(start_n, max_n + 1, step_n):
        for i in range(reps):
            elapsed_time = time.time() - t1
            m, s = divmod(elapsed_time, 60)
            h, m = divmod(m, 60)
            print "\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
            print name
            print u"├── n=%d\n├── rep=%d\n└── elapsed time %d:%02d:%02d \n" % (n, i + 1, h, m, s)

            success = False
            failure_count[(n, i)] = 0
            failure_OPT_count[(n, i)] = 0
            while success == False:
                ins = ii.sim_instance_ev_scheduling_fixed_intervals(scenario=scenario, n=n, capacity=capacity)

                sol_round = oo.round_EV_scheduling_fixed_interval(ins)  # PTAS
                sol_opt = sol_round.frac_sol  # gurobi relaxed

                if sol_opt.succeed == False:
                    failure_OPT_count[(n, i)] += 1
                    print "\n─── too small obj: [retry count %d]\n" % failure_OPT_count[(n, i)]
                    elapsed_time = time.time() - t1
                    m, s = divmod(elapsed_time, 60)
                    h, m = divmod(m, 60)
                    print name
                    print u"├── n=%d\n├── rep=%d\n└── elapsed time %d:%02d:%02d \n" % (n, i + 1, h, m, s)
                    continue
                ##############
                #solution_x_k[(n - start_n + step_n) / step_n - 1, i] = sol_opt.x[n, c]
                ### OPT
                frac_OPT_EV_time[(n - start_n + step_n) / step_n - 1, i] = sol_opt.running_time
                frac_OPT_EV_obj[(n - start_n + step_n) / step_n - 1, i] = sol_opt.obj
                frac_OPT_EV_num_of_constraints[
                    (n - start_n + step_n) / step_n - 1, i] = sol_opt.number_of_constraints_paper_formulation
                print "OPT obj:              %15.2f  |  time: %5.3f" % (
                    sol_opt.obj, sol_opt.running_time)

                ### round_EV
                sol_round.ar = sol_round.ar
                print "round_EV obj:        %15.2f  |  time: %5.3f  |  [AR: %5.3f ]" % (
                    sol_round.obj, sol_round.running_time, sol_round.ar)

                round_EV_obj[(n - start_n + step_n) / step_n - 1, i] = sol_round.obj
                round_EV_time[(n - start_n + step_n) / step_n - 1, i] = sol_round.running_time
                round_EV_ar[(n - start_n + step_n) / step_n - 1, i] = sol_round.ar
                round_EV_frac_x_count[(n - start_n + step_n) / step_n - 1, i] = sol_round.frac_x_comp_count
                round_EV_frac_com_percentage[(n - start_n + step_n) / step_n - 1, i] = (
                                                                                               sol_round.frac_x_comp_count + sol_round.frac_x_comp_count) / float(
                    sol_opt.number_of_constraints_paper_formulation)

                ##############
                if sol_opt.succeed == False or sol_round.succeed == False:
                    failure_count[(n, i)] += 1
                    print "\n─── Failure in solving one of the problems: [retry count %d]" % failure_count[(n, i)]
                    print "sol_opt.succeed: ", sol_opt.succeed
                    print "sol_round.succeed: ", sol_round.succeed
                    print ''

                    elapsed_time = time.time() - t1
                    m, s = divmod(elapsed_time, 60)
                    h, m = divmod(m, 60)
                    print name
                    print u"├── n=%d\n├── rep=%d\n└── elapsed time %d:%02d:%02d \n" % (n, i + 1, h, m, s)
                    continue
                success = True
                print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"

        # intermediate saving
        fin_time = time.time() - t1
        if dry_run == False:
            np.savez(dump_dir + name,
                     failure_count=failure_count,
                     failure_EV_count=failure_OPT_count,
                     round_EV_obj=round_EV_obj,
                     round_EV_ar=round_EV_ar,
                     round_EV_time=round_EV_time,
                     round_EV_frac_x_count=round_EV_frac_x_count,
                     round_EV_frac_com_percentage=round_EV_frac_com_percentage,
                     frac_EV_obj=frac_OPT_EV_obj,
                     frac_EV_time=frac_OPT_EV_time,
                     frac_OPT_EV_num_of_constraints=frac_OPT_EV_num_of_constraints,
                     fin_time=fin_time)

    m, s = divmod(fin_time, 60)
    h, m = divmod(m, 60)
    print "\n=== simulation finished in %d:%02d:%02d ===\n" % (h, m, s)

    return name


# sim for EV-scheduling (E-Energy 2018) #Greedy
def sim_ev(scenario="L", max_n=1000, step_n=50, start_n=100, reps=40, capacity=1000000, dry_run=False,
           dump_dir="results/dump/"):
    name = "EV:[%s]__alg4_max_n=%d_step_n=%d_start_n=%d_reps=%d_capacity=%d" % (
        scenario, max_n, step_n, start_n, reps, capacity)
    ### set up variables
    assert (max_n % step_n == 0)
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)

    t1 = time.time()
    #####

    round_EV_obj = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    round_EV_time = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    round_EV_ar = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    round_EV_frac_x_count = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    round_EV_frac_y_count = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    round_EV_frac_com_percentage = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    round_EV_x_down_count = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    round_EV_x_up_count = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    round_EV_count_y_due_to_rounded_x = np.zeros(((max_n - start_n + step_n) / step_n, reps))

    frac_OPT_EV_obj = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    frac_OPT_EV_time = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    frac_OPT_EV_num_of_constraints = np.zeros(((max_n - start_n + step_n) / step_n, reps))

    failure_count = {}
    failure_OPT_count = {}
    Solution_x_k = {}
    for n in range(start_n, max_n + 1, step_n):
        for i in range(reps):
            elapsed_time = time.time() - t1
            m, s = divmod(elapsed_time, 60)
            h, m = divmod(m, 60)
            print "\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
            print name
            print u"├── n=%d\n├── rep=%d\n└── elapsed time %d:%02d:%02d \n" % (n, i + 1, h, m, s)

            success = False
            failure_count[(n, i)] = 0
            failure_OPT_count[(n, i)] = 0
            while success == False:
                ins = ii.sim_instance_ev_scheduling(scenario=scenario, n=n, capacity=capacity)

                sol_round = oo.round_EV_scheduling4(ins)
                sol_opt = sol_round.frac_sol

                if sol_opt.succeed == False:
                    failure_OPT_count[(n, i)] += 1
                    print "\n─── too small obj: [retry count %d]\n" % failure_OPT_count[(n, i)]
                    elapsed_time = time.time() - t1
                    m, s = divmod(elapsed_time, 60)
                    h, m = divmod(m, 60)
                    print name
                    print u"├── n=%d\n├── rep=%d\n└── elapsed time %d:%02d:%02d \n" % (n, i + 1, h, m, s)
                    continue
                ##############

                ### OPT
                frac_OPT_EV_time[(n - start_n + step_n) / step_n - 1, i] = sol_opt.running_time
                frac_OPT_EV_obj[(n - start_n + step_n) / step_n - 1, i] = sol_opt.obj
                frac_OPT_EV_num_of_constraints[
                    (n - start_n + step_n) / step_n - 1, i] = sol_opt.number_of_constraints_paper_formulation
                print "OPT obj:              %15.2f  |  time: %5.3f" % (
                    sol_opt.obj, sol_opt.running_time)

                ### round_EV
                sol_round.ar = sol_round.ar
                print "round_EV obj:        %15.2f  |  time: %5.3f  |  [AR: %5.3f ]" % (
                    sol_round.obj, sol_round.running_time, sol_round.ar)

                round_EV_obj[(n - start_n + step_n) / step_n - 1, i] = sol_round.obj
                round_EV_time[(n - start_n + step_n) / step_n - 1, i] = sol_round.running_time
                round_EV_ar[(n - start_n + step_n) / step_n - 1, i] = sol_round.ar
                round_EV_frac_x_count[(n - start_n + step_n) / step_n - 1, i] = sol_round.frac_x_comp_count
                round_EV_frac_y_count[(n - start_n + step_n) / step_n - 1, i] = sol_round.frac_y_comp_count
                round_EV_frac_com_percentage[(n - start_n + step_n) / step_n - 1, i] = (
                                                                                               sol_round.frac_x_comp_count + sol_round.frac_x_comp_count) / float(
                    sol_opt.number_of_constraints_paper_formulation)
                round_EV_x_down_count[(n - start_n + step_n) / step_n - 1, i] = sol_round.rounded_up_count
                round_EV_x_up_count[(n - start_n + step_n) / step_n - 1, i] = sol_round.rounded_down_count
                round_EV_count_y_due_to_rounded_x[(n - start_n + step_n) / step_n - 1, i] = sol_round.ar

                ##############
                if sol_opt.succeed == False or sol_round.succeed == False:
                    failure_count[(n, i)] += 1
                    print "\n─── Failure in solving one of the problems: [retry count %d]" % failure_count[(n, i)]
                    print "sol_opt.succeed: ", sol_opt.succeed
                    print "sol_round.succeed: ", sol_round.succeed
                    print ''

                    elapsed_time = time.time() - t1
                    m, s = divmod(elapsed_time, 60)
                    h, m = divmod(m, 60)
                    print name
                    print u"├── n=%d\n├── rep=%d\n└── elapsed time %d:%02d:%02d \n" % (n, i + 1, h, m, s)
                    continue
                success = True
                print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"

        # intermediate saving
        fin_time = time.time() - t1
        if dry_run == False:
            np.savez(dump_dir + name,
                     failure_count=failure_count,
                     failure_EV_count=failure_OPT_count,
                     round_EV_obj=round_EV_obj,
                     round_EV_ar=round_EV_ar,
                     round_EV_time=round_EV_time,
                     round_EV_frac_x_count=round_EV_frac_x_count,
                     round_EV_frac_y_count=round_EV_frac_y_count,
                     round_EV_frac_com_percentage=round_EV_frac_com_percentage,
                     round_EV_x_down_count=round_EV_x_down_count,
                     round_EV_x_up_count=round_EV_x_up_count,
                     round_EV_count_y_due_to_rounded_x=round_EV_count_y_due_to_rounded_x,
                     frac_EV_obj=frac_OPT_EV_obj,
                     frac_EV_time=frac_OPT_EV_time,
                     frac_OPT_EV_num_of_constraints=frac_OPT_EV_num_of_constraints,
                     fin_time=fin_time,
                     )

    m, s = divmod(fin_time, 60)
    h, m = divmod(m, 60)
    print "\n=== simulation finished in %d:%02d:%02d ===\n" % (h, m, s)

    return name


######################################################
######################################################
######################################################
######################################################
######################################################
# sim for scheduling
def sim_FnT(scenario="FCR", F_percentage=0.0, max_n=3500, step_n=100, start_n=100, reps=40, dry_run=False,
            dump_dir="results/dump/"):
    name = "FnT:[%s]__F_percentage=%.2f_max_n=%d_step_n=%d_start_n=%d_reps=%d" % (
        scenario, F_percentage, max_n, step_n, start_n, reps)
    ### set up variables
    assert (max_n % step_n == 0)
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)

    cons = ''
    t1 = time.time()
    #####

    round_OPF_obj = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    round_OPF_time = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    round_OPF_frac_count = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    round_OPF_frac_percentage = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    round_OPF_ar = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    round_OPF_ar2 = np.zeros(((max_n - start_n + step_n) / step_n, reps))

    no_LP_round_OPF_obj = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    no_LP_round_OPF_time = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    no_LP_round_OPF_ar = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    no_LP_round_OPF_frac_count = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    no_LP_round_OPF_frac_percentage = np.zeros(((max_n - start_n + step_n) / step_n, reps))

    frac_OPF_obj = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    frac_OPF_time = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    frac_OPF_ar = np.zeros(((max_n - start_n + step_n) / step_n, reps))

    OPT_time = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    OPT_obj = np.zeros(((max_n - start_n + step_n) / step_n, reps))

    failure_count = {}
    failure_OPT_count = {}

    for n in range(start_n, max_n + 1, step_n):
        for i in range(reps):
            elapsed_time = time.time() - t1
            m, s = divmod(elapsed_time, 60)
            h, m = divmod(m, 60)
            print "\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
            print name
            print u"├── n=%d\n├── rep=%d\n└── elapsed time %d:%02d:%02d \n" % (n, i + 1, h, m, s)

            success = False
            failure_count[(n, i)] = 0
            failure_OPT_count[(n, i)] = 0
            while success == False:

                ins = ii.sim_instance_sch(scenario=scenario, n=n, F_percentage=F_percentage)

                ### opt
                sol_opt = oo.max_sOPF_OPT(ins)
                OPT_time[(n - start_n + step_n) / step_n - 1, i] = sol_opt.running_time
                OPT_obj[(n - start_n + step_n) / step_n - 1, i] = sol_opt.obj
                if sol_opt.succeed == False:
                    failure_OPT_count[(n, i)] += 1
                    print "\n─── too small obj: [retry count %d]\n" % failure_OPT_count[(n, i)]
                    elapsed_time = time.time() - t1
                    m, s = divmod(elapsed_time, 60)
                    h, m = divmod(m, 60)
                    print name
                    print u"├── n=%d\n├── rep=%d\n└── elapsed time %d:%02d:%02d \n" % (n, i + 1, h, m, s)
                    continue

                print "OPT obj:              %15.2f  |  time: %5.3f" % (
                    sol_opt.obj, sol_opt.running_time)
                ##############

                ### frac_OPF
                sol_frac = oo.max_sOPF_OPT(ins, fractional=True)
                # some times the fractional is not well-rounded
                if sol_frac > sol_opt:
                    sol_frac.obj = sol_opt.obj
                sol_frac.ar = sol_frac.obj / sol_opt.obj
                print "frac_OPF obj:         %15.2f  |  time: %5.3f  |  [AR: %5.3f ]" % (
                    sol_frac.obj, sol_frac.running_time, sol_frac.ar)

                frac_OPF_obj[(n - start_n + step_n) / step_n - 1, i] = sol_frac.obj
                frac_OPF_time[(n - start_n + step_n) / step_n - 1, i] = sol_frac.running_time
                frac_OPF_ar[(n - start_n + step_n) / step_n - 1, i] = sol_frac.ar
                ##############

                ### round_OPF
                sol_round = oo.round_OPF(ins)
                sol_round.ar = sol_round.obj / sol_opt.obj
                sol_round.ar2 = sol_round.obj / sol_frac.obj
                print "round_OPF obj:        %15.2f  |  time: %5.3f  |  [AR: %5.3f ]" % (
                    sol_round.obj, sol_round.running_time, sol_round.ar)

                round_OPF_obj[(n - start_n + step_n) / step_n - 1, i] = sol_round.obj
                round_OPF_time[(n - start_n + step_n) / step_n - 1, i] = sol_round.running_time
                round_OPF_ar[(n - start_n + step_n) / step_n - 1, i] = sol_round.ar
                round_OPF_ar2[(n - start_n + step_n) / step_n - 1, i] = sol_round.ar2
                round_OPF_frac_count[(n - start_n + step_n) / step_n - 1, i] = sol_round.frac_comp_count
                round_OPF_frac_percentage[(n - start_n + step_n) / step_n - 1, i] = sol_round.frac_comp_percentage

                ##############

                ### no LP round_OPF
                sol_no_LP = oo.round_OPF(ins, use_LP=False)
                sol_no_LP.ar = sol_no_LP.obj / sol_opt.obj
                print "round_no_LP_OPF obj:  %15.2f  |  time: %5.3f  |  [AR: %5.3f ]" % (
                    sol_no_LP.obj, sol_no_LP.running_time, sol_no_LP.ar)

                no_LP_round_OPF_obj[(n - start_n + step_n) / step_n - 1, i] = sol_no_LP.obj
                no_LP_round_OPF_time[(n - start_n + step_n) / step_n - 1, i] = sol_no_LP.running_time
                no_LP_round_OPF_ar[(n - start_n + step_n) / step_n - 1, i] = sol_no_LP.ar
                no_LP_round_OPF_frac_count[(n - start_n + step_n) / step_n - 1, i] = sol_no_LP.frac_comp_count
                no_LP_round_OPF_frac_percentage[(n - start_n + step_n) / step_n - 1, i] = sol_no_LP.frac_comp_percentage
                ##############

                if sol_opt.succeed == False or sol_round.succeed == False or sol_no_LP.succeed == False or sol_frac == False:
                    failure_count[(n, i)] += 1
                    print "\n─── Failure in solving one of the problems: [retry count %d]" % failure_count[(n, i)]
                    print "sol_opt.succeed: ", sol_opt.succeed
                    print "sol_round.succeed: ", sol_round.succeed
                    print "sol_no_LP.succeed: ", sol_no_LP.succeed
                    print "sol_frac.succeed: ", sol_frac.succeed
                    print ''

                    elapsed_time = time.time() - t1
                    m, s = divmod(elapsed_time, 60)
                    h, m = divmod(m, 60)
                    print name
                    print u"├── n=%d\n├── rep=%d\n└── elapsed time %d:%02d:%02d \n" % (n, i + 1, h, m, s)
                    continue
                success = True
                print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"

        # intermediate saving
        if dry_run == False:
            np.savez(dump_dir + name,
                     failure_count=failure_count,
                     failure_OPF_count=failure_OPT_count,
                     round_OPF_obj=round_OPF_obj,
                     round_OPF_ar=round_OPF_ar,
                     round_OPF_ar2=round_OPF_ar2,
                     round_OPF_time=round_OPF_time,
                     round_OPF_frac_count=round_OPF_frac_count,
                     round_OPF_frac_percentage=round_OPF_frac_percentage,
                     no_LP_round_OPF_obj=no_LP_round_OPF_obj,
                     no_LP_round_OPF_ar=no_LP_round_OPF_ar,
                     no_LP_round_OPF_time=no_LP_round_OPF_time,
                     no_LP_round_OPF_frac_count=no_LP_round_OPF_frac_count,
                     no_LP_round_OPF_frac_percentage=no_LP_round_OPF_frac_percentage,
                     frac_OPF_obj=frac_OPF_obj,
                     frac_OPF_ar=frac_OPF_ar,
                     frac_OPF_time=frac_OPF_time,
                     OPT_obj=OPT_obj,
                     OPT_time=OPT_time)
    x = np.arange(start_n, max_n + 1, step_n)
    x = x.reshape((len(x), 1))

    mean_yerr_round_OPF_obj = np.append(x, np.array(map(lambda y: u.mean_yerr(y), round_OPF_obj)), 1)
    mean_yerr_round_OPF_ar = np.append(x, np.array(map(lambda y: u.mean_yerr(y), round_OPF_ar)), 1)
    mean_yerr_round_OPF_ar2 = np.append(x, np.array(map(lambda y: u.mean_yerr(y), round_OPF_ar2)), 1)
    mean_yerr_round_OPF_time = np.append(x, np.array(map(lambda y: u.mean_yerr(y), round_OPF_time)), 1)
    mean_yerr_round_OPF_frac_count = np.append(x, np.array(map(lambda y: u.mean_yerr(y), round_OPF_frac_count)), 1)
    mean_yerr_round_OPF_frac_percentage = np.append(x,
                                                    np.array(map(lambda y: u.mean_yerr(y), round_OPF_frac_percentage)),
                                                    1)

    mean_yerr_no_LP_round_OPF_obj = np.append(x, np.array(map(lambda y: u.mean_yerr(y), no_LP_round_OPF_obj)), 1)
    mean_yerr_no_LP_round_OPF_ar = np.append(x, np.array(map(lambda y: u.mean_yerr(y), no_LP_round_OPF_ar)), 1)
    mean_yerr_no_LP_round_OPF_time = np.append(x, np.array(map(lambda y: u.mean_yerr(y), no_LP_round_OPF_time)), 1)
    mean_yerr_no_LP_round_OPF_frac_count = np.append(x, np.array(
        map(lambda y: u.mean_yerr(y), no_LP_round_OPF_frac_count)), 1)
    mean_yerr_no_LP_round_OPF_frac_percentage = np.append(x, np.array(
        map(lambda y: u.mean_yerr(y), no_LP_round_OPF_frac_percentage)), 1)

    mean_yerr_frac_OPF_obj = np.append(x, np.array(map(lambda y: u.mean_yerr(y), frac_OPF_obj)), 1)
    mean_yerr_frac_OPF_ar = np.append(x, np.array(map(lambda y: u.mean_yerr(y), frac_OPF_ar)), 1)
    mean_yerr_frac_OPF_time = np.append(x, np.array(map(lambda y: u.mean_yerr(y), frac_OPF_time)), 1)

    mean_yerr_OPT_obj = np.append(x, np.array(map(lambda y: u.mean_yerr(y), OPT_obj)), 1)
    mean_yerr_OPT_time = np.append(x, np.array(map(lambda y: u.mean_yerr(y), OPT_time)), 1)

    print mean_yerr_round_OPF_ar

    if dry_run == False:
        np.savez(dump_dir + name,
                 failure_count=failure_count,
                 failure_OPF_count=failure_OPT_count,
                 round_OPF_obj=round_OPF_obj,
                 round_OPF_ar=round_OPF_ar,
                 round_OPF_ar2=round_OPF_ar2,
                 round_OPF_time=round_OPF_time,
                 round_OPF_frac_count=round_OPF_frac_count,
                 round_OPF_frac_percentage=round_OPF_frac_percentage,
                 no_LP_round_OPF_obj=no_LP_round_OPF_obj,
                 no_LP_round_OPF_ar=no_LP_round_OPF_ar,
                 no_LP_round_OPF_time=no_LP_round_OPF_time,
                 no_LP_round_OPF_frac_count=no_LP_round_OPF_frac_count,
                 no_LP_round_OPF_frac_percentage=no_LP_round_OPF_frac_percentage,
                 OPT_obj=OPT_obj,
                 OPT_time=OPT_time,
                 frac_OPF_obj=frac_OPF_obj,
                 frac_OPF_ar=frac_OPF_ar,
                 frac_OPF_time=frac_OPF_time,
                 mean_yerr_round_OPF_obj=mean_yerr_round_OPF_obj,
                 mean_yerr_round_OPF_ar=mean_yerr_round_OPF_ar,
                 mean_yerr_round_OPF_ar2=mean_yerr_round_OPF_ar2,
                 mean_yerr_round_OPF_time=mean_yerr_round_OPF_time,
                 mean_yerr_round_OPF_frac_count=mean_yerr_round_OPF_frac_count,
                 mean_yerr_round_OPF_frac_percentage=mean_yerr_round_OPF_frac_percentage,
                 mean_yerr_no_LP_round_OPF_obj=mean_yerr_no_LP_round_OPF_obj,
                 mean_yerr_no_LP_round_OPF_ar=mean_yerr_no_LP_round_OPF_ar,
                 mean_yerr_no_LP_round_OPF_time=mean_yerr_no_LP_round_OPF_time,
                 mean_yerr_no_LP_round_OPF_frac_count=mean_yerr_no_LP_round_OPF_frac_count,
                 mean_yerr_no_LP_round_OPF_frac_percentage=mean_yerr_no_LP_round_OPF_frac_percentage,
                 mean_yerr_frac_OPF_obj=mean_yerr_frac_OPF_obj,
                 mean_yerr_frac_OPF_ar=mean_yerr_frac_OPF_ar,
                 mean_yerr_frac_OPF_time=mean_yerr_frac_OPF_time,
                 mean_yerr_OPT_obj=mean_yerr_OPT_obj,
                 mean_yerr_OPT_time=mean_yerr_OPT_time)
    fin_time = time.time() - t1
    m, s = divmod(fin_time, 60)
    h, m = divmod(m, 60)
    print "\n=== simulation finished in %d:%02d:%02d ===\n" % (h, m, s)

    return name


#############################################
#############################################
#############################################
#############################################
#############################################
def sim_TCNS18_PTAS(scenario="FCR", max_resample=100, n=2500, F_percentage=0.0, max_e=.9, step_e=.1, start_e=.1,
                    reps=40, dry_run=False,
                    dump_dir="results/dump/", topology=123):
    name = "TCNS18_PTAS:[%s]__topology=%d__max_resample=%d__n=%d__F_percentage=%.2f_max_e=%.2f_step_e=%.2f_start_e=%.2f_reps=%d" % (
        scenario, topology, max_resample, n, F_percentage, max_e, step_e, start_e, reps)
    ### set up variables
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)

    cons = ''
    t1 = time.time()
    #####

    num_rows = int((max_e + step_e) / step_e) - 1
    round_OPF_obj = np.zeros((num_rows, reps))
    round_OPF_time = np.zeros((num_rows, reps))
    round_OPF_frac_count = np.zeros((num_rows, reps))
    round_OPF_frac_percentage = np.zeros((num_rows, reps))
    round_OPF_ar = np.zeros((num_rows, reps))
    round_OPF_ar2 = np.zeros((num_rows, reps))
    round_OPF_try_count = np.zeros((num_rows, reps))

    no_LP_round_OPF_obj = np.zeros((num_rows, reps))
    no_LP_round_OPF_time = np.zeros((num_rows, reps))
    no_LP_round_OPF_ar = np.zeros((num_rows, reps))
    no_LP_round_OPF_try_count = np.zeros((num_rows, reps))
    no_LP_round_OPF_frac_count = np.zeros((num_rows, reps))
    no_LP_round_OPF_frac_percentage = np.zeros((num_rows, reps))

    frac_OPF_obj = np.zeros((num_rows, reps))
    frac_OPF_time = np.zeros((num_rows, reps))
    frac_OPF_ar = np.zeros((num_rows, reps))

    OPT_time = np.zeros((num_rows, reps))
    OPT_obj = np.zeros((num_rows, reps))
    OPT_ones_count = np.zeros((num_rows, reps))

    failure_count = {}
    failure_less_then_one_opt_obj_count = {}

    for e in np.arange(start_e, max_e + step_e, step_e):
        for i in np.arange(reps):
            elapsed_time = time.time() - t1
            m, s = divmod(elapsed_time, 60)
            h, m = divmod(m, 60)
            row = int((e - start_e + step_e) / step_e - 1)
            print "\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
            print name
            print u"├── e=%1.2f\n├── rep=%d\n└── elapsed time %d:%02d:%02d \n" % (e, i + 1, h, m, s)

            success = False
            failure_count[(e, i)] = 0
            failure_less_then_one_opt_obj_count[(e, i)] = 0
            while success == False:
                T = None
                if topology == 13:
                    T = ii.network_csv_load(filename='test-feeders/13-node.csv')
                elif topology == 123:
                    T = ii.network_csv_load(filename='test-feeders/feeder123-ieee.csv')

                ins = ii.sim_instance(T, scenario=scenario, n=n, F_percentage=F_percentage)

                ### opt
                sol_opt = oo.min_OPF_OPT(ins, epsilon=e)
                OPT_time[row, i] = sol_opt.running_time
                OPT_obj[row, i] = sol_opt.obj
                OPT_ones_count[row, i] = sol_opt.ones_comp_count

                print "OPT obj:              %15.2f  |  time: %5.3f" % (
                    sol_opt.obj, sol_opt.running_time)
                ##############

                ### frac_OPF
                sol_frac = oo.min_OPF_OPT(ins, fractional=True)
                # some times the fractional is not well-rounded
                if sol_frac > sol_opt:
                    sol_frac.obj = sol_opt.obj
                if -ins.rounding_tolerance <= sol_opt.obj <= ins.rounding_tolerance:
                    sol_frac.ar = 1
                else:
                    sol_frac.ar = sol_frac.obj / sol_opt.obj
                print "frac_OPF obj:         %15.2f  |  time: %5.3f  |  [AR: %5.3f ]" % (
                    sol_frac.obj, sol_frac.running_time, sol_frac.ar)

                frac_OPF_obj[row, i] = sol_frac.obj
                frac_OPF_time[row, i] = sol_frac.running_time
                frac_OPF_ar[row, i] = sol_frac.ar
                ##############

                ### round_OPF
                sol_round = oo.PTAS_rand_sample(ins, epsilon=e, max_tries=max_resample)
                if -ins.rounding_tolerance <= sol_opt.obj <= ins.rounding_tolerance or -ins.rounding_tolerance <= sol_round.obj <= ins.rounding_tolerance:
                    sol_round.obj = 0
                    sol_round.ar = 1
                    sol_round.ar2 = 1
                else:
                    sol_round.ar = sol_round.obj / sol_opt.obj
                    sol_round.ar2 = sol_round.obj / sol_frac.obj
                print "round_OPF obj:        %15.2f  |  time: %5.3f  |  [AR: %5.3f ]" % (
                    sol_round.obj, sol_round.running_time, sol_round.ar)

                round_OPF_obj[row, i] = sol_round.obj
                round_OPF_time[row, i] = sol_round.running_time
                round_OPF_ar[row, i] = sol_round.ar
                round_OPF_ar2[row, i] = sol_round.ar2
                round_OPF_try_count[row, i] = sol_round.try_count
                if -ins.rounding_tolerance <= sol_opt.obj <= ins.rounding_tolerance or -ins.rounding_tolerance <= sol_round.obj <= ins.rounding_tolerance:
                    round_OPF_frac_count[row, i] = 0
                    round_OPF_frac_percentage[row, i] = 0
                else:
                    round_OPF_frac_count[row, i] = sol_round.frac_comp_count
                    round_OPF_frac_percentage[row, i] = sol_round.frac_comp_percentage
                ##############

                ### no LP round_OPF
                sol_no_LP = oo.PTAS_rand_sample(ins, use_LP=False, epsilon=e, max_tries=max_resample)
                if -ins.rounding_tolerance <= sol_opt.obj <= ins.rounding_tolerance or -ins.rounding_tolerance <= sol_no_LP.obj <= ins.rounding_tolerance:
                    sol_no_LP.ar = 1
                    sol_no_LP.obj = 0
                else:
                    sol_no_LP.ar = sol_no_LP.obj / sol_opt.obj
                print "round_no_LP_OPF obj:  %15.2f  |  time: %5.3f  |  [AR: %5.3f ]" % (
                    sol_no_LP.obj, sol_no_LP.running_time, sol_no_LP.ar)

                no_LP_round_OPF_obj[row, i] = sol_no_LP.obj
                no_LP_round_OPF_time[row, i] = sol_no_LP.running_time
                no_LP_round_OPF_ar[row, i] = sol_no_LP.ar
                no_LP_round_OPF_try_count[row, i] = sol_no_LP.try_count
                no_LP_round_OPF_frac_count[row, i] = sol_no_LP.frac_comp_count
                no_LP_round_OPF_frac_percentage[row, i] = sol_no_LP.frac_comp_percentage
                ##############

                if sol_opt.succeed == False or sol_round.succeed == False or sol_no_LP.succeed == False or sol_frac == False or sol_round.obj < sol_frac.obj:
                    failure_count[(e, i)] += 1
                    print "\n─── Failure in solving one of the problems: [retry count %d]" % failure_count[(e, i)]
                    print "sol_opt.succeed: ", sol_opt.succeed
                    print "sol_round.succeed: ", sol_round.succeed
                    print "sol_no_LP.succeed: ", sol_no_LP.succeed
                    print "sol_frac.succeed: ", sol_frac.succeed
                    print "frac < round: ", sol_round.obj > sol_frac.obj
                    print ''

                    elapsed_time = time.time() - t1
                    m, s = divmod(elapsed_time, 60)
                    h, m = divmod(m, 60)
                    print name
                    print u"├── e=%.2f\n├── rep=%d\n└── elapsed time %d:%02d:%02d \n" % (e, i + 1, h, m, s)
                    continue
                success = True
                print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"

            # intermediate saving
            if dry_run == False:
                np.savez(dump_dir + name,
                         failure_count=failure_count,
                         failure_less_then_one_opt_obj_count=failure_less_then_one_opt_obj_count,
                         round_OPF_obj=round_OPF_obj,
                         round_OPF_ar=round_OPF_ar,
                         round_OPF_ar2=round_OPF_ar2,
                         round_OPF_time=round_OPF_time,
                         round_OPF_frac_count=round_OPF_frac_count,
                         round_OPF_frac_percentage=round_OPF_frac_percentage,
                         no_LP_round_OPF_obj=no_LP_round_OPF_obj,
                         no_LP_round_OPF_ar=no_LP_round_OPF_ar,
                         no_LP_round_OPF_time=no_LP_round_OPF_time,
                         no_LP_round_OPF_frac_count=no_LP_round_OPF_frac_count,
                         no_LP_round_OPF_frac_percentage=no_LP_round_OPF_frac_percentage,
                         frac_OPF_obj=frac_OPF_obj,
                         frac_OPF_ar=frac_OPF_ar,
                         frac_OPF_time=frac_OPF_time,
                         OPT_obj=OPT_obj,
                         OPT_ones_count=OPT_ones_count,
                         OPT_time=OPT_time)
    fin_time = time.time() - t1
    m, s = divmod(fin_time, 60)
    h, m = divmod(m, 60)
    print "\n=== simulation finished in %d:%02d:%02d ===\n" % (h, m, s)

    return name


######################################################
######################################################
######################################################
######################################################
######################################################
# topology = [13 | 123]
def sim_TCNS18(scenario="FCR", alg='PTAS', max_resample=10, epsilon=0.1, F_percentage=0.0, max_n=3500, step_n=100,
               start_n=100, reps=40, dry_run=False,
               dump_dir="results/dump/", topology=123):
    if alg == 'PTAS':
        name = "TCNS18:[%s]__max_resample=%d__epsilon=%1.2f__topology=%d__F_percentage=%.2f_max_n=%d_step_n=%d_start_n=%d_reps=%d" % (
            scenario, max_resample, epsilon, topology, F_percentage, max_n, step_n, start_n, reps)
    else:
        name = "TCNS18:[%s]__topology=%d__F_percentage=%.2f_max_n=%d_step_n=%d_start_n=%d_reps=%d" % (
            scenario, topology, F_percentage, max_n, step_n, start_n, reps)
    ### set up variables
    assert (max_n % step_n == 0)
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)

    cons = ''
    t1 = time.time()
    #####

    round_OPF_obj = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    round_OPF_time = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    round_OPF_frac_count = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    round_OPF_frac_percentage = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    round_OPF_ar = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    round_OPF_ar2 = np.zeros(((max_n - start_n + step_n) / step_n, reps))

    no_LP_round_OPF_obj = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    no_LP_round_OPF_time = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    no_LP_round_OPF_ar = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    no_LP_round_OPF_frac_count = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    no_LP_round_OPF_frac_percentage = np.zeros(((max_n - start_n + step_n) / step_n, reps))

    frac_OPF_obj = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    frac_OPF_time = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    frac_OPF_ar = np.zeros(((max_n - start_n + step_n) / step_n, reps))

    OPT_time = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    OPT_obj = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    OPT_ones_count = np.zeros(((max_n - start_n + step_n) / step_n, reps))

    failure_count = {}
    failure_less_then_one_opt_obj_count = {}

    for n in range(start_n, max_n + 1, step_n):
        for i in range(reps):
            elapsed_time = time.time() - t1
            m, s = divmod(elapsed_time, 60)
            h, m = divmod(m, 60)
            print "\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
            print name
            print u"├── n=%d\n├── rep=%d\n└── elapsed time %d:%02d:%02d \n" % (n, i + 1, h, m, s)

            success = False
            failure_count[(n, i)] = 0
            failure_less_then_one_opt_obj_count[(n, i)] = 0
            while success == False:
                T = None
                if topology == 13:
                    T = ii.network_csv_load(filename='test-feeders/13-node.csv')
                elif topology == 123:
                    T = ii.network_csv_load(filename='test-feeders/feeder123-ieee.csv')

                ins = ii.sim_instance(T, scenario=scenario, n=n, F_percentage=F_percentage)

                ### opt
                sol_opt = oo.min_OPF_OPT(ins)
                OPT_time[(n - start_n + step_n) / step_n - 1, i] = sol_opt.running_time
                OPT_obj[(n - start_n + step_n) / step_n - 1, i] = sol_opt.obj
                OPT_ones_count[(n - start_n + step_n) / step_n - 1, i] = sol_opt.ones_comp_count
                # if sol_opt.obj < 1:
                #     failure_less_then_one_opt_obj_count[(n,i)] += 1
                #     print "\n─── too small obj: [retry count %d]\n" % failure_less_then_one_opt_obj_count[(n,i)]
                #     elapsed_time = time.time() - t1
                #     m, s = divmod(elapsed_time, 60)
                #     h, m = divmod(m, 60)
                #     print name
                #     print u"├── n=%d\n├── rep=%d\n└── elapsed time %d:%02d:%02d \n" % (n, i + 1, h, m, s)
                #     continue

                print "OPT obj:              %15.2f  |  time: %5.3f" % (
                    sol_opt.obj, sol_opt.running_time)
                ##############

                ### frac_OPF
                sol_frac = oo.min_OPF_OPT(ins, fractional=True)
                # some times the fractional is not well-rounded
                if sol_frac > sol_opt:
                    sol_frac.obj = sol_opt.obj
                if -ins.rounding_tolerance <= sol_opt.obj <= ins.rounding_tolerance:
                    sol_frac.ar = 1
                else:
                    sol_frac.ar = sol_frac.obj / sol_opt.obj
                print "frac_OPF obj:         %15.2f  |  time: %5.3f  |  [AR: %5.3f ]" % (
                    sol_frac.obj, sol_frac.running_time, sol_frac.ar)

                frac_OPF_obj[(n - start_n + step_n) / step_n - 1, i] = sol_frac.obj
                frac_OPF_time[(n - start_n + step_n) / step_n - 1, i] = sol_frac.running_time
                frac_OPF_ar[(n - start_n + step_n) / step_n - 1, i] = sol_frac.ar
                ##############

                ### round_OPF
                if alg == "PTAS":
                    sol_round = oo.PTAS_rand_sample(ins, epsilon=epsilon, max_tries=max_resample)
                else:
                    sol_round = oo.round_OPF(ins, frac_sol=sol_frac)

                if -ins.rounding_tolerance <= sol_opt.obj <= ins.rounding_tolerance or -ins.rounding_tolerance <= sol_round.obj <= ins.rounding_tolerance:
                    sol_round.obj = 0
                    sol_round.ar = 1
                    sol_round.ar2 = 1
                else:
                    sol_round.ar = sol_round.obj / sol_opt.obj
                    sol_round.ar2 = sol_round.obj / sol_frac.obj
                print "round_OPF obj:        %15.2f  |  time: %5.3f  |  [AR: %5.3f ]" % (
                    sol_round.obj, sol_round.running_time, sol_round.ar)

                round_OPF_obj[(n - start_n + step_n) / step_n - 1, i] = sol_round.obj
                round_OPF_time[(n - start_n + step_n) / step_n - 1, i] = sol_round.running_time
                round_OPF_ar[(n - start_n + step_n) / step_n - 1, i] = sol_round.ar
                round_OPF_ar2[(n - start_n + step_n) / step_n - 1, i] = sol_round.ar2
                if -ins.rounding_tolerance <= sol_opt.obj <= ins.rounding_tolerance or -ins.rounding_tolerance <= sol_round.obj <= ins.rounding_tolerance:
                    round_OPF_frac_count[(n - start_n + step_n) / step_n - 1, i] = 0
                    round_OPF_frac_percentage[(n - start_n + step_n) / step_n - 1, i] = 0
                else:
                    round_OPF_frac_count[(n - start_n + step_n) / step_n - 1, i] = sol_round.frac_comp_count
                    round_OPF_frac_percentage[(n - start_n + step_n) / step_n - 1, i] = sol_round.frac_comp_percentage
                ##############

                ### no LP round_OPF
                if alg == "PTAS":
                    sol_no_LP = oo.PTAS_rand_sample(ins, epsilon=epsilon, max_tries=max_resample, use_LP=False)
                else:
                    sol_no_LP = oo.round_OPF(ins, frac_sol=sol_frac, use_LP=False)

                if -ins.rounding_tolerance <= sol_opt.obj <= ins.rounding_tolerance or -ins.rounding_tolerance <= sol_no_LP.obj <= ins.rounding_tolerance:
                    sol_no_LP.ar = 1
                    sol_no_LP.obj = 0
                else:
                    sol_no_LP.ar = sol_no_LP.obj / sol_opt.obj
                print "round_no_LP_OPF obj:  %15.2f  |  time: %5.3f  |  [AR: %5.3f ]" % (
                    sol_no_LP.obj, sol_no_LP.running_time, sol_no_LP.ar)

                no_LP_round_OPF_obj[(n - start_n + step_n) / step_n - 1, i] = sol_no_LP.obj
                no_LP_round_OPF_time[(n - start_n + step_n) / step_n - 1, i] = sol_no_LP.running_time
                no_LP_round_OPF_ar[(n - start_n + step_n) / step_n - 1, i] = sol_no_LP.ar
                no_LP_round_OPF_frac_count[(n - start_n + step_n) / step_n - 1, i] = sol_no_LP.frac_comp_count
                no_LP_round_OPF_frac_percentage[(n - start_n + step_n) / step_n - 1, i] = sol_no_LP.frac_comp_percentage
                ##############

                if sol_opt.succeed == False or sol_round.succeed == False or sol_no_LP.succeed == False or sol_frac == False or sol_round.obj < sol_frac.obj:
                    failure_count[(n, i)] += 1
                    print "\n─── Failure in solving one of the problems: [retry count %d]" % failure_count[(n, i)]
                    print "sol_opt.succeed: ", sol_opt.succeed
                    print "sol_round.succeed: ", sol_round.succeed
                    print "sol_no_LP.succeed: ", sol_no_LP.succeed
                    print "sol_frac.succeed: ", sol_frac.succeed
                    print "frac < round: ", sol_round.obj < sol_frac.obj
                    print ''

                    elapsed_time = time.time() - t1
                    m, s = divmod(elapsed_time, 60)
                    h, m = divmod(m, 60)
                    print name
                    print u"├── n=%d\n├── rep=%d\n└── elapsed time %d:%02d:%02d \n" % (n, i + 1, h, m, s)
                    continue
                success = True
                print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"

        # intermediate saving
        if dry_run == False:
            np.savez(dump_dir + name,
                     failure_count=failure_count,
                     failure_less_then_one_opt_obj_count=failure_less_then_one_opt_obj_count,
                     round_OPF_obj=round_OPF_obj,
                     round_OPF_ar=round_OPF_ar,
                     round_OPF_ar2=round_OPF_ar2,
                     round_OPF_time=round_OPF_time,
                     round_OPF_frac_count=round_OPF_frac_count,
                     round_OPF_frac_percentage=round_OPF_frac_percentage,
                     no_LP_round_OPF_obj=no_LP_round_OPF_obj,
                     no_LP_round_OPF_ar=no_LP_round_OPF_ar,
                     no_LP_round_OPF_time=no_LP_round_OPF_time,
                     no_LP_round_OPF_frac_count=no_LP_round_OPF_frac_count,
                     no_LP_round_OPF_frac_percentage=no_LP_round_OPF_frac_percentage,
                     frac_OPF_obj=frac_OPF_obj,
                     frac_OPF_ar=frac_OPF_ar,
                     frac_OPF_time=frac_OPF_time,
                     OPT_obj=OPT_obj,
                     OPT_ones_count=OPT_ones_count,
                     OPT_time=OPT_time)
    x = np.arange(start_n, max_n + 1, step_n)
    x = x.reshape((len(x), 1))

    mean_yerr_round_OPF_obj = np.append(x, np.array(map(lambda y: u.mean_yerr(y), round_OPF_obj)), 1)
    mean_yerr_round_OPF_ar = np.append(x, np.array(map(lambda y: u.mean_yerr(y), round_OPF_ar)), 1)
    mean_yerr_round_OPF_ar2 = np.append(x, np.array(map(lambda y: u.mean_yerr(y), round_OPF_ar2)), 1)
    mean_yerr_round_OPF_time = np.append(x, np.array(map(lambda y: u.mean_yerr(y), round_OPF_time)), 1)
    mean_yerr_round_OPF_frac_count = np.append(x, np.array(map(lambda y: u.mean_yerr(y), round_OPF_frac_count)), 1)
    mean_yerr_round_OPF_frac_percentage = np.append(x,
                                                    np.array(map(lambda y: u.mean_yerr(y), round_OPF_frac_percentage)),
                                                    1)

    mean_yerr_no_LP_round_OPF_obj = np.append(x, np.array(map(lambda y: u.mean_yerr(y), no_LP_round_OPF_obj)), 1)
    mean_yerr_no_LP_round_OPF_ar = np.append(x, np.array(map(lambda y: u.mean_yerr(y), no_LP_round_OPF_ar)), 1)
    mean_yerr_no_LP_round_OPF_time = np.append(x, np.array(map(lambda y: u.mean_yerr(y), no_LP_round_OPF_time)), 1)
    mean_yerr_no_LP_round_OPF_frac_count = np.append(x, np.array(
        map(lambda y: u.mean_yerr(y), no_LP_round_OPF_frac_count)), 1)
    mean_yerr_no_LP_round_OPF_frac_percentage = np.append(x, np.array(
        map(lambda y: u.mean_yerr(y), no_LP_round_OPF_frac_percentage)), 1)

    mean_yerr_frac_OPF_obj = np.append(x, np.array(map(lambda y: u.mean_yerr(y), frac_OPF_obj)), 1)
    mean_yerr_frac_OPF_ar = np.append(x, np.array(map(lambda y: u.mean_yerr(y), frac_OPF_ar)), 1)
    mean_yerr_frac_OPF_time = np.append(x, np.array(map(lambda y: u.mean_yerr(y), frac_OPF_time)), 1)

    mean_yerr_OPT_obj = np.append(x, np.array(map(lambda y: u.mean_yerr(y), OPT_obj)), 1)
    mean_yerr_OPT_time = np.append(x, np.array(map(lambda y: u.mean_yerr(y), OPT_time)), 1)

    print mean_yerr_round_OPF_ar

    if dry_run == False:
        np.savez(dump_dir + name,
                 failure_count=failure_count,
                 failure_less_then_one_opt_obj_count=failure_less_then_one_opt_obj_count,
                 round_OPF_obj=round_OPF_obj,
                 round_OPF_ar=round_OPF_ar,
                 round_OPF_ar2=round_OPF_ar2,
                 round_OPF_time=round_OPF_time,
                 round_OPF_frac_count=round_OPF_frac_count,
                 round_OPF_frac_percentage=round_OPF_frac_percentage,
                 no_LP_round_OPF_obj=no_LP_round_OPF_obj,
                 no_LP_round_OPF_ar=no_LP_round_OPF_ar,
                 no_LP_round_OPF_time=no_LP_round_OPF_time,
                 no_LP_round_OPF_frac_count=no_LP_round_OPF_frac_count,
                 no_LP_round_OPF_frac_percentage=no_LP_round_OPF_frac_percentage,
                 OPT_obj=OPT_obj,
                 OPT_ones_count=OPT_ones_count,
                 OPT_time=OPT_time,
                 frac_OPF_obj=frac_OPF_obj,
                 frac_OPF_ar=frac_OPF_ar,
                 frac_OPF_time=frac_OPF_time,
                 mean_yerr_round_OPF_obj=mean_yerr_round_OPF_obj,
                 mean_yerr_round_OPF_ar=mean_yerr_round_OPF_ar,
                 mean_yerr_round_OPF_ar2=mean_yerr_round_OPF_ar2,
                 mean_yerr_round_OPF_time=mean_yerr_round_OPF_time,
                 mean_yerr_round_OPF_frac_count=mean_yerr_round_OPF_frac_count,
                 mean_yerr_round_OPF_frac_percentage=mean_yerr_round_OPF_frac_percentage,
                 mean_yerr_no_LP_round_OPF_obj=mean_yerr_no_LP_round_OPF_obj,
                 mean_yerr_no_LP_round_OPF_ar=mean_yerr_no_LP_round_OPF_ar,
                 mean_yerr_no_LP_round_OPF_time=mean_yerr_no_LP_round_OPF_time,
                 mean_yerr_no_LP_round_OPF_frac_count=mean_yerr_no_LP_round_OPF_frac_count,
                 mean_yerr_no_LP_round_OPF_frac_percentage=mean_yerr_no_LP_round_OPF_frac_percentage,
                 mean_yerr_frac_OPF_obj=mean_yerr_frac_OPF_obj,
                 mean_yerr_frac_OPF_ar=mean_yerr_frac_OPF_ar,
                 mean_yerr_frac_OPF_time=mean_yerr_frac_OPF_time,
                 mean_yerr_OPT_obj=mean_yerr_OPT_obj,
                 mean_yerr_OPT_time=mean_yerr_OPT_time)
    fin_time = time.time() - t1
    m, s = divmod(fin_time, 60)
    h, m = divmod(m, 60)
    print "\n=== simulation finished in %d:%02d:%02d ===\n" % (h, m, s)

    return name


######################################################
######################################################
######################################################
######################################################
######################################################

# topology = [38 | 123] (IEEE topology. The code can be cleaned up in future, only csv file should be given)
# greedy algorithm
def sim_TCNS16(scenario="FCR", F_percentage=0.0, max_n=1500, step_n=100, start_n=100, reps=40, dry_run=True,
               dump_dir="results/dump/", is_adaptive_loss=True, topology=123):
    name = "%s__topology=%d__F_percentage=%.2f_max_n=%d_step_n=%d_start_n=%d_reps=%d" % (
        scenario, topology, F_percentage, max_n, step_n, start_n, reps)
    if is_adaptive_loss:
        name = "adapt__%s__topology=%d__F_percentage=%.2f_max_n=%d_step_n=%d_start_n=%d_reps=%d" % (
            scenario, topology, F_percentage, max_n, step_n, start_n, reps)
    ### set up variables
    cons = ''
    capacity_flag = 'C_'
    loss_ratio = .08
    loss_step = .005
    if is_adaptive_loss: loss_ratio = 0
    t1 = time.time()
    #####

    assert (max_n % step_n == 0)

    greedy_obj = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    greedy_time = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    greedy_ar = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    greedy_ar2 = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    adaptive_greedy_loss_ratio = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    adaptive_OPT_s_loss_ratio = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    sub_optimal1_count_per_iteration = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    sub_optimal2_count_per_iteration = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    opt_err_count_per_iteration = np.zeros(((max_n - start_n + step_n) / step_n, reps))

    greedy_group_count = np.zeros(((max_n - start_n + step_n) / step_n, reps))

    OPT_s_time = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    OPT_s_obj = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    OPT_time = np.zeros(((max_n - start_n + step_n) / step_n, reps))
    OPT_obj = np.zeros(((max_n - start_n + step_n) / step_n, reps))

    for n in range(start_n, max_n + 1, step_n):
        for i in range(reps):
            elapsed_time = time.time() - t1
            m, s = divmod(elapsed_time, 60)
            h, m = divmod(m, 60)
            print "\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
            print name
            print u"├── n=%d\n├── rep=%d\n└── elapsed time %d:%02d:%02d \n" % (n, i + 1, h, m, s)
            print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
            T = None
            if topology == 38:
                # T = ii.network_38node(loss_ratio=loss_ratio)
                pass
            elif topology == 123:
                T = ii.network_csv_load(filename='test-feeders/123-node-line-data.csv', loss_ratio=loss_ratio)

            is_OPT_smaller = True

            suboptimal1_count = 0
            suboptimal2_count = 0
            opt_err_count = 0
            while is_OPT_smaller:
                ins = ii.sim_instance(T, scenario=scenario, n=n, F_percentage=F_percentage, capacity_flag=capacity_flag)
                ### opt
                sol_opt = oo.max_OPF_OPT(ins, cons)
                print "OPT obj   :    %15.2f  |  time: %5.3f" % (
                    sol_opt.obj, sol_opt.running_time)
                ### opt(s)
                sol_opt_s = None
                if is_adaptive_loss:
                    sol_opt_s = ss.adaptive_OPT(ins, cons=cons)
                else:
                    sol_opt_s = ss.OPT(ins, cons=cons, capacity_flag=capacity_flag)

                ####### replace if OPTs is bigger
                if sol_opt_s.obj > sol_opt.obj:
                    sol_opt.obj = sol_opt_s.obj
                    sol_opt.x = sol_opt_s.x

                OPT_time[(n - start_n + step_n) / step_n - 1, i] = sol_opt.running_time
                OPT_obj[(n - start_n + step_n) / step_n - 1, i] = sol_opt.obj
                OPT_s_time[(n - start_n + step_n) / step_n - 1, i] = sol_opt_s.running_time
                OPT_s_obj[(n - start_n + step_n) / step_n - 1, i] = sol_opt_s.obj

                print "OPTs obj  :    %15.2f  |  time: %5.3f" % (
                    sol_opt_s.obj, sol_opt_s.running_time)

                ### greedy
                sol = None
                if is_adaptive_loss:
                    sol = ss.adaptive_greedy(ins, cons=cons, loss_step=loss_step)
                elif F_percentage == 0:
                    sol = ss.greedy(ins, capacity_flag=capacity_flag, cons=cons)
                else:
                    sol = ss.mixed_greedy(ins, capacity_flag=capacity_flag, cons=cons)
                sol.ar = sol.obj / sol_opt.obj
                sol.ar2 = sol.obj / sol_opt_s.obj
                print "Greedy obj:    %15.2f  |  time: %5.3f  |  AR (OPT, OPTs): %5.3f, %4.3f (%d groups)" % (
                    sol.obj, sol.running_time, sol.ar, sol.ar2, len(sol.groups))

                if sol.ar > 1 or sol.ar2 > 1:  # or sol_opt_s.obj/sol_opt.obj > 1  :
                    if sol.ar > 1: suboptimal1_count += 1
                    if sol.ar2 > 1: suboptimal2_count += 1
                    # if sol_opt_s.obj/sol_opt.obj > 1: opt_err_count += 1
                    print '\n----- repeating (#Grd>OPT = %d, #Grd>OPTs = %d, #OPTs>OPT = %d): invalid OPT --------' % (
                        suboptimal1_count, suboptimal2_count, opt_err_count)
                    print name
                    print u"├── n=%d\n├── rep=%d\n└── elapsed time %d:%02d:%02d \n" % (n, i + 1, h, m, s)

                    continue
                else:
                    is_OPT_smaller = False

                greedy_obj[(n - start_n + step_n) / step_n - 1, i] = sol.obj
                greedy_time[(n - start_n + step_n) / step_n - 1, i] = sol.running_time
                greedy_ar[(n - start_n + step_n) / step_n - 1, i] = sol.ar
                greedy_ar2[(n - start_n + step_n) / step_n - 1, i] = sol.ar2
                greedy_group_count[(n - start_n + step_n) / step_n - 1, i] = len(sol.groups)
                sub_optimal1_count_per_iteration[(n - start_n + step_n) / step_n - 1, i] = suboptimal1_count
                sub_optimal2_count_per_iteration[(n - start_n + step_n) / step_n - 1, i] = suboptimal2_count
                opt_err_count_per_iteration[(n - start_n + step_n) / step_n - 1, i] = opt_err_count
                if is_adaptive_loss:
                    adaptive_greedy_loss_ratio[(n - start_n + step_n) / step_n - 1, i] = sol.loss_ratio
                    adaptive_OPT_s_loss_ratio[(n - start_n + step_n) / step_n - 1, i] = sol_opt_s.loss_ratio
        # intermediate saving
        if dry_run == False:
            np.savez(dump_dir + name,
                     greedy_obj=greedy_obj,
                     greedy_ar=greedy_ar,
                     greedy_ar2=greedy_ar2,
                     greedy_time=greedy_time,
                     greedy_group_count=greedy_group_count,
                     sub_optimal1_count_per_iteration=sub_optimal1_count_per_iteration,
                     sub_optimal2_count_per_iteration=sub_optimal2_count_per_iteration,
                     opt_err_count_per_iteration=opt_err_count_per_iteration,
                     adaptive_greedy_loss_ratio=adaptive_greedy_loss_ratio,
                     adaptive_OPT_s_loss_ratio=adaptive_OPT_s_loss_ratio,
                     OPT_obj=OPT_obj,
                     OPT_time=OPT_time,
                     OPT_s_obj=OPT_s_obj,
                     OPT_s_time=OPT_s_time)
    x = np.arange(start_n, max_n + 1, step_n)
    x = x.reshape((len(x), 1))

    mean_yerr_greedy_time = np.append(x, np.array(map(lambda y: u.mean_yerr(y), greedy_time)), 1)
    mean_yerr_OPT_time = np.append(x, np.array(map(lambda y: u.mean_yerr(y), OPT_time)), 1)
    mean_yerr_OPT_s_time = np.append(x, np.array(map(lambda y: u.mean_yerr(y), OPT_s_time)), 1)
    mean_yerr_greedy_ar = np.append(x, np.array(map(lambda y: u.mean_yerr(y), greedy_ar)), 1)
    mean_yerr_greedy_ar2 = np.append(x, np.array(map(lambda y: u.mean_yerr(y), greedy_ar2)), 1)
    mean_yerr_greedy_group_count = np.append(x, np.array(map(lambda y: u.mean_yerr(y), greedy_group_count)), 1)

    mean_yerr_greedy_obj = np.append(x, np.array(map(lambda y: u.mean_yerr(y), greedy_obj)), 1)
    mean_yerr_OPT_obj = np.append(x, np.array(map(lambda y: u.mean_yerr(y), OPT_obj)), 1)
    mean_yerr_OPT_s_obj = np.append(x, np.array(map(lambda y: u.mean_yerr(y), OPT_s_obj)), 1)

    print mean_yerr_greedy_ar

    if dry_run == False:
        np.savez(dump_dir + name,
                 greedy_obj=greedy_obj,
                 greedy_ar=greedy_ar,
                 greedy_ar2=greedy_ar2,
                 greedy_time=greedy_time,
                 greedy_group_count=greedy_group_count,
                 sub_optimal1_count_per_iteration=sub_optimal1_count_per_iteration,
                 sub_optimal2_count_per_iteration=sub_optimal2_count_per_iteration,
                 opt_err_count_per_iteration=opt_err_count_per_iteration,
                 adaptive_greedy_loss_ratio=adaptive_greedy_loss_ratio,
                 adaptive_OPT_s_loss_ratio=adaptive_OPT_s_loss_ratio,
                 OPT_obj=OPT_obj,
                 OPT_time=OPT_time,
                 OPT_s_obj=OPT_s_obj,
                 OPT_s_time=OPT_s_time,
                 mean_yerr_greedy_ar=mean_yerr_greedy_ar,
                 mean_yerr_greedy_ar2=mean_yerr_greedy_ar2,
                 mean_yerr_greedy_time=mean_yerr_greedy_time,
                 mean_yerr_greedy_group_count=mean_yerr_greedy_group_count,
                 mean_yerr_OPT_time=mean_yerr_OPT_time,
                 mean_yerr_OPT_s_time=mean_yerr_OPT_s_time,
                 mean_yerr_greedy_obj=mean_yerr_greedy_obj,
                 mean_yerr_OPT_obj=mean_yerr_OPT_obj,
                 mean_yerr_OPT_s_obj=mean_yerr_OPT_s_obj)
    fin_time = time.time() - t1
    m, s = divmod(fin_time, 60)
    h, m = divmod(m, 60)
    print "\n=== simulation finished in %d:%02d:%02d ===\n" % (h, m, s)

    return name


if __name__ == "__main__":
    # import logging
    # logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    sim_ev_fixed_interval(scenario="L", max_n=1000, step_n=100, start_n=50, reps=40, capacity=1000000, dry_run=False)
    #sim_TCNS18_PTAS(scenario="FCR", max_resample=100, n=2500, F_percentage=0.0, max_e=.9, step_e=.1, start_e=.1,
    #                    reps=40, dry_run=False, topology=123)
    #(scenario="L", max_n=1000, step_n=50, start_n=100, reps=40, capacity=1000000, dry_run=False,)
