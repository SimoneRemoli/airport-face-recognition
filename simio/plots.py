import datetime

import numpy as np
from matplotlib import dates as mdates

from sim.autoscaler import AutoScaler
from sim.welford import estimate


def plot_inf_seq(stats: dict, pc=False, qos=False, name=""):
    fig, ax = plt.subplots()
    plotliste = []
    asse_x = []
    accum = []
    for k, v in stats.items():
        if not pc:
            asse_x.append(k.lambda_value)
        else:
            asse_x.append(k.pc)
    if not pc:
        extra = "(pc=0.4)"
    else:
        extra = "(lambda=1.4 req/s)"
    plt.title("Tempo di risposta class-E " + extra)
    plt.xticks(asse_x)
    yerre = []
    for k, v in stats.items():
        plotliste.append(np.average(v["edge_waits_E"]))
        accum.append(v["edge_waits_E"])
        yerre.append(estimate(v["edge_waits_E"][1:])[2])
    ax.plot(asse_x, plotliste, marker="o")
    plt.grid()
    if qos:
        ax.hlines(y=3, xmin=min(asse_x), xmax=max(asse_x),
                  color='r', linestyle='dashed', linewidth=1, label=f"QoS")
    if not pc:
        plt.xlabel("tasso arrivi [req/s]")
    else:
        plt.xlabel("p_c")

    plt.errorbar(asse_x, plotliste, yerr=yerre, fmt='o', color='blue',
                 ecolor='black', capsize=7, label='Media con Intervallo Confidenza 95%')

    plt.ylabel("tempo di risposta class-E [s]")
    if name == "inf_lambda": plt.ylim(bottom=0)
    print(plotliste)
    print(yerre)
    plt.savefig("plots/" + name + ".svg")


def plot_TA(lb, stats, name=""):
    fig, ax = plt.subplots()

    base_date_for_mdates = datetime.datetime(2000, 1, 1, 0, 0, 0)
    accum_series = []
    all_plot_x_converted_values = []
    for k, v in stats.items():
        # riduzione artificiale
        v["times_sampling"] = v["times_sampling"][:int(len(v["times_sampling"]) / 4) + 1]
        v["edge_waits_E"] = v["edge_waits_E"][:int(len(v["edge_waits_E"]) / 4) + 1]
        plot_x_original_seconds = [item for item in v["times_sampling"]]
        plot_x_mdates_format = [mdates.date2num(base_date_for_mdates + datetime.timedelta(seconds=s))
                                for s in plot_x_original_seconds]
        accum_series.append(v["edge_waits_E"])
        ax.plot(plot_x_mdates_format, v["edge_waits_E"], label="seed=" + str(v["seed"]), marker='.', markersize=6,
                linestyle='-')
        all_plot_x_converted_values.extend(plot_x_mdates_format)  # Raccogli i valori convertiti
    ax.set_xlim(min(all_plot_x_converted_values), max(all_plot_x_converted_values))

    ax.xaxis.set_major_locator(mdates.HourLocator(interval=4))

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    ax.set_title('Analisi del transitorio')
    ax.legend()
    ax.xaxis.set_visible(True)
    plt.ylabel("Tempo di risposta class-E [s]")
    ax.grid(True)
    avg, _, w = estimate([np.average(a) for a in accum_series])
    print(avg, w)
    plt.savefig("plots/" + name + ".svg")


def plot_finito(lb, stats, qos=True, fasce=False, name=""):
    for type in ["edge_waits_E", "edge_waits_C", "edge_waits"]:
        fig, ax = plt.subplots()

        base_date_for_mdates = datetime.datetime(2000, 1, 1, 0, 0, 0)

        all_plot_x_converted_values = []
        max_x_value_for_ticks = 0
        plot_x_mdates_format = []
        accum_series = []
        for k, v in stats.items():
            plot_x_original_seconds = [item for item in v["times_sampling"]]
            plot_x_mdates_format = [mdates.date2num(base_date_for_mdates + datetime.timedelta(seconds=s))
                                    for s in plot_x_original_seconds]
            accum_series.append(v[type])
            ax.plot(plot_x_mdates_format, v[type], linestyle='-')

            all_plot_x_converted_values.extend(plot_x_mdates_format)

            if plot_x_mdates_format:
                if plot_x_mdates_format[-1] > max_x_value_for_ticks:
                    max_x_value_for_ticks = plot_x_mdates_format[-1]

        if qos:
            ax.hlines(y=3, xmin=min(plot_x_mdates_format), xmax=max(plot_x_mdates_format),
                      color='r', linestyle='dashed', linewidth=1, label=f"QoS")

        ax.set_xlim(min(all_plot_x_converted_values), max(all_plot_x_converted_values))

        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

        current_ticks_num = list(ax.get_xticks())
        midnight_next_day_num = mdates.date2num(base_date_for_mdates + datetime.timedelta(days=1))

        if midnight_next_day_num not in current_ticks_num:
            current_ticks_num.append(midnight_next_day_num)
            current_ticks_num.sort()
            ax.set_xticks(current_ticks_num)

        if fasce:
            for ore in [6, 12, 18, 22]:
                vline_time = mdates.date2num(base_date_for_mdates + datetime.timedelta(hours=ore))
                ax.axvline(x=vline_time, color='green', linestyle='--', linewidth=1.5)

        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

        ax.set_xlabel("Tempo [hh:mm]")

        if type == "edge_waits": type_hr = ""
        if type == "edge_waits_E": type_hr = " (class-E)"
        if type == "edge_waits_C": type_hr = " (class-C)"

        plt.ylabel("Tempo di risposta nodo Edge" + type_hr + " [s]")
        ax.grid(True)
        avg, _, w = estimate([np.average(a) for a in accum_series])
        print(avg, w)
        plt.savefig("plots/" + name + "-" + type + ".svg")


import matplotlib.pyplot as plt


def plot_scaling(stats: dict, name=""):
    fig, ax = plt.subplots()

    base_date_for_mdates = datetime.datetime(2000, 1, 1, 0, 0, 0)

    all_plot_x_converted_values = []
    max_x_value_for_ticks = 0
    plot_x_mdates_format = []
    accum_series = []
    asc = AutoScaler(0, 1, 4, 0.4)
    for k, v in stats.items():
        plot_x_original_seconds = [item for item in v["times_sampling"]]
        plot_x_mdates_format = [mdates.date2num(base_date_for_mdates + datetime.timedelta(seconds=s))
                                for s in plot_x_original_seconds]

        all_plot_x_converted_values.extend(plot_x_mdates_format)

        if plot_x_mdates_format:
            if plot_x_mdates_format[-1] > max_x_value_for_ticks:
                max_x_value_for_ticks = plot_x_mdates_format[-1]

    ax.set_xlim(min(all_plot_x_converted_values), max(all_plot_x_converted_values))

    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

    current_ticks_num = list(ax.get_xticks())
    midnight_next_day_num = mdates.date2num(base_date_for_mdates + datetime.timedelta(days=1))

    if midnight_next_day_num not in current_ticks_num:
        current_ticks_num.append(midnight_next_day_num)
        current_ticks_num.sort()
        ax.set_xticks(current_ticks_num)

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    ax.set_xlabel("Tempo [hh:mm]")

    plt.tight_layout()
    for _, v in stats.items():
        stats = v
        break
    i = -1
    colors = ["c", "m", "y"]
    for thr in range(3):
        i += 1
        ax.hlines(y=asc.get_thresholds()[thr], xmin=0, xmax=max(current_ticks_num), color=colors[i], linestyle='dotted',
                  linewidth=1, label=f"{i} server(s)")
    index = 0 if name == "pc1" else 1
    ax.plot(plot_x_mdates_format[index:], v["scalability_lambda"], linestyle='-', label="effettivo")
    y = [asc.get_thresholds()[i] for i in v["scalability_edgeno"]]
    ax.plot(plot_x_mdates_format[index:], y, color='r', linestyle='dashed', label="soglia limite")

    for ore in [6, 12, 18, 22]:
        vline_time = mdates.date2num(base_date_for_mdates + datetime.timedelta(hours=ore))
        ax.axvline(x=vline_time, color='green', linestyle='--', linewidth=1.5)
    plt.ylabel("Tasso di arrivi [req/s]")
    plt.legend(title="Tasso di arrivi")
    avg, _, w = estimate([np.average(a) for a in accum_series])
    print(avg, w)
    plt.savefig("plots/scaling" + name + ".svg")
