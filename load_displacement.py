import pandas as pd
import re
import matplotlib.pyplot as plt

report_file = "abaqus.rpt"  # must match the report file
x_label = "U2"
y_label = "RF2"
title = "Title"  # the label and title for the data
interactive = True  # display interactive charts vs only saving the file
save_fig = False  # save graphs automatically to /plots/ with the title in the filename
node_list = []  # specify individual nodes to plot on the graph.
#                 Leave as an empty list if you want everything
plot_timesteps = False  # Will plot the timesteps for each data point on the plot.
#                        This is very slow and should not be used with a large number of nodes


df0 = pd.read_table(report_file, header=[0, 1], engine="python", sep=r"\s{2,}")
# anything separated by more than 2 spaces interpreted as column separator
# you will have to change the header lines to match the report file
# You also need to pad the left-most column with extra rows to match the rest of the data
# or else your labels will be off by 1

df0.columns = df0.columns.map("".join)
# unwrap the column names from the abaqus report

df0 = df0.set_index(df0.columns[0])
# set firsst column to be the index. We don't really need to keep it, but it contains
# timestep info which might be useful for debugging

# separate the two kinds of data by field labels given at the top of this file
x = df0.filter(regex=x_label)
y = df0.filter(regex=y_label)

magic_regex = lambda x: re.findall(r"(.+) (PI.+)N:\s?(\d+)", x)  # find node number
# broken into 3 search groups:
# the type of xydata (S:S22)
# the part id (PI: PART-1-1)
# and the node id (14642)
node_num = lambda x: magic_regex(x)[0][2]  # get the node id only


x = x.rename(node_num, axis="columns")
y = y.rename(node_num, axis="columns")
# strips all but the node numbers off the headers

# We need to delete columns with the same header,
# not sure why there are even duplicates in the first place.
x = x.loc[:, ~x.columns.duplicated()]
y = y.loc[:, ~y.columns.duplicated()]

node_list = [str(x) for x in node_list]
# the node column headers are strings, so we need to convert

if not node_list:  # if not specified, use all nodes
    node_list = x.columns

print(
    f"There are {len(node_list)} nodes and {len(df0.index)} increments in this anaylsis,"
)

for node in node_list:
    plt.plot(x[node], y[node])
    plt.text(x[node].iloc[-1], y[node].iloc[-1], node)
    # label the end of each line with the node number

    # the following will add timesteps to each point. Will make plot very crowded and sluggish
    if plot_timesteps:
        for x_coord, y_coord, timestep in zip(x[node], y[node], range(len(x[node]))):
            # extract individual x and y coordinates, along with their location, which represents their timestep
            plt.text(x_coord, y_coord, str(timestep))

plt.title(title)
plt.ylabel(y_label)
plt.xlabel(x_label)
if save_fig:
    plt.savefig(f"./plots/{title}-Per Node.png")
if interactive:
    plt.show()
plt.close()

# Plot average graphs
plt.plot(x.mean(axis="columns"), y.mean(axis="columns"))

plt.ylabel(y_label)
# Use the label from the first column
plt.xlabel(x_label)
# use the label from the last column

plt.title(title)

# Uncomment this stuff if you want the linear regression slope included on the graph
# from scipy.stats import linregress
# slope = linregress(x.mean(axis="columns"), y.mean(axis="columns")).slope
# plt.text(
#     x=0.5,
#     y=0.1,
#     s=f"slope={slope}",
#     horizontalalignment="center",
#     verticalalignment="center",
#     transform=plt.gca().transAxes,  # make the posistions relative to plot instead of relative to data
# )

if save_fig:
    plt.savefig(f"./plots/{title}-Average.png")
if interactive:
    plt.show()
plt.close()