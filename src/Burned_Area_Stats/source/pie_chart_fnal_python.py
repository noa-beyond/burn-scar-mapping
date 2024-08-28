# Δημιουργία διαγράμματος pie chart για την απεικόνηση ποσοστών ανα χρήση γης μιας καμμένης περιοχής

# Εισαγωγή βιβλιωθηκών
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from matplotlib.gridspec import GridSpec
import json


class PlotCLC:
    def __init__(self, CorineLandCover_PATH, CorineLandCover_JSON_PATH):
        self.file_path = CorineLandCover_PATH  # Αλλάξτε τη διαδρομή στο αρχείο σας


        with open(CorineLandCover_JSON_PATH, 'r', encoding='utf-8') as fp:
            self.CLC_number_to_legend_color = json.load(fp)

        # make the CorinaLandCover Plot
        self.MakePlot(self.file_path, self.CLC_number_to_legend_color)





    def MakePlot(self, file_path, dictionary):
        # Λεξικό με τις κατηγορίες του Corine Land Cover
        # Δημιουργία ενός λεξικού που αντιστοιχίζει αριθμούς με χρώματα σε μορφή HEX
        # Κωδικός , Χρώμα, Όνομα κατηγορίας

        code, percentage, colors, labels, removed_labels = self.read_csv_and_prepare_data(self.file_path, dictionary)
        print(f"Οι κωδικοί είναι: {code} \n"
              f"Τα ποσοστά είναι: {percentage} \n"
              f"Τα χρώματα είναι: {colors} \n"
              f"Οι κατηγορίες είναι: {labels}")

        #self.pie_chart(percentage, colors, labels, os.path.basename(file_path).replace(".csv", ".png"))
        #self.create_legend(labels, colors)
        self.combined_pie_and_legend(percentage, colors, labels, removed_labels, file_path)


    # Συνάρτηση get_color_and_category
    # Εισάγωντας τον κωδικό μιας κατηγορίας του CLC επιστρέφει το χρώμα της και το ονομά της

    # Συνάρτηση που επιστρέφει το χρώμα που αντιστοιχεί σε έναν αριθμό
    def get_color_and_category(self, code, dictionary):
        code = str(code)
        if code in dictionary:
            color, category_eng, category_gr = dictionary[code]
            return color, category_eng, category_gr
        else:
            return None, "Μη έγκυρος αριθμός"


    # Παράδειγμα χρήσης της συνάρτησης
    #number1 = 323
    #color1, category2 = get_color_and_category(number1)
    #print(f"Το χρώμα και η κατηγορία που αντιστοιχεί στον κωδικό {number1} είναι: {color1}, {category2}")


    # Έλεγχος data frame
    def data_frame_check(self, data_frame):
        # Εκτύπωση του αρχικού data frame
        print(f"Αρχικό data frame:\n{data_frame}\n")

        # Συγκέντρωση ποσοστών για διπλές καταχωρήσεις
        data_frame = data_frame.groupby("Code", as_index=False).agg({"Percentage": "sum"})
        print(f"Μετά συγχώνευσης διπλών καταχωρήσεων:\n{data_frame}\n")

        # Έλεγχος και διόρθωση του συνολικού ποσοστού
        total_percentage = data_frame["Percentage"].sum()
        print(f"Percentage_sum {total_percentage}\n")
        if total_percentage < 1:
            additional_row1 = pd.DataFrame({"Code": [000], "Percentage": [1 - total_percentage]})
            data_frame = pd.concat([data_frame, additional_row1], ignore_index=True)
            print(f"Μετά προσθήκης ποσοστού:\n{data_frame}\n")
        elif total_percentage > 1:
            print("Το άθροισμα των ποσοστών είναι μεγαλύτερο από 100%")
            print(f"Σύνολο ποσοστών: {total_percentage}\n")
            return None

        # Αφαίρεση ποσοστών κάτω του 3%
        percentage_sum = 0
        to_remove = []
        removed = []  # Κωδικοί που θα αφαιρεθούν
        for i in range(len(data_frame["Percentage"])):
            if data_frame["Percentage"][i] < 0.03:
                percentage_sum += data_frame["Percentage"][i]
                removed.append(data_frame["Code"][i])
                to_remove.append(i)

        # Αφαίρεση των γραμμών που έχουν μικρό ποσοστό
        data_frame = data_frame.drop(to_remove)

        # Προσθήκη γραμμής για το σύνολο των μικρών ποσοστών
        if percentage_sum > 0:
            additional_row = pd.DataFrame({"Code": [000], "Percentage": [percentage_sum]})
            data_frame = pd.concat([data_frame, additional_row], ignore_index=True)

        # Επιστροφή του επεξεργασμένου DataFrame
        print(f"Τελικό:\n{data_frame}\n")
        return data_frame, removed  # Επιστροφή του επεξεργασμένου DataFrame


    # Συνάρτηση για την εισαγωγή δεδομένων απεικόνισης

    def read_csv_and_prepare_data(self, file_path, dictionary):
        # Διαβάζουμε τα δεδομένα από το CSV αρχείο
        data_frame = pd.read_csv(file_path, header=None, names=["Code", "Percentage"])
        data_frame['Percentage'] = data_frame['Percentage'] / 100

        data_frame_checked, removed_codes = self.data_frame_check(data_frame)

        # Δημιουργία λιστών για τους κωδικούς και τα ποσοστά
        code = data_frame_checked["Code"].tolist()
        percentage = data_frame_checked["Percentage"].tolist()
        colors = []
        labels = []
        removed_labels = []

        # Λήψη χρωμάτων και ετικετών για κάθε κωδικό
        for number in code:
            color, description_eng, description_gr = self.get_color_and_category(number, dictionary)
            description = description_eng
            if color and description:
                labels.append(description)
                colors.append(color)

        # Λήψη ετικετών για κάθε κωδικό που αφαιρέθηκε
        for number in removed_codes:
            color, description_eng, description_gr = self.get_color_and_category(number, dictionary)
            description = description_eng
            if color and description:
                removed_labels.append(description + '\n')

        removed_labels[-1] = removed_labels[-1].rstrip('\n') # remove last \n from last description
        removed_labels[-2] = removed_labels[-2].rstrip('\n') # remove last \n from last description


        return code, percentage, colors, labels, removed_labels

    # Συνάρτηση διαγράμματος πίτας
    def pie_chart(self, percentage_d, colors_d, labels_d, path_file):
        plt.figure(figsize=(12, 12))
        plt.pie(percentage_d,
                labels=labels_d,
                colors=colors_d,
                startangle=140,
                autopct='%1.1f%%',
                textprops={'family': 'sans-serif', 'fontsize': 12}
                )
        plt.title("Καμμένες εκτάσεις - Χρήσεις γης Corine Land Cover 2018",
                  fontdict={'family': 'sans-serif', 'fontsize': 20, 'fontweight': 'bold'},
                  loc='right',
                  pad=30)
        plt.axis('equal')  # Ισότροπος άξονας για κυκλική πίτα
        # Αποθήκευση του διαγράμματος ως εικόνα
        plt.savefig(path_file, format='png', bbox_inches='tight')
        plt.show()


    def create_legend(self, labels_d, colors_d):
        fig, ax = plt.subplots(figsize=(6, 6))
        patches = [plt.Line2D([0], [0], marker='o', color='w', label=label, markersize=10, markerfacecolor=color)
                   for label, color in zip(labels_d, colors_d)]
        legend = ax.legend(
            handles=patches,
            loc='center',
            fontsize=12,
            title="Κατηγορίες Χρήσης Γης",
            shadow=False
        )
        legend.set_title("Κατηγορίες Χρήσης Γης", prop={'size': '14', 'weight': 'bold'})
        ax.axis('off')  # Απενεργοποίηση των αξόνων
        plt.show()

    def combined_pie_and_legend(self, percentage_d, colors_d, labels_d, removed_labels, path_file):
        fig = plt.figure(figsize=(15, 6))  # Adjusted to give more width for the legend
        gs = GridSpec(1, 2, width_ratios=[2, 0.5])  # 1 row, 2 columns; first column 2 times wider than the second

        # Pie chart
        ax1 = fig.add_subplot(gs[0])
        ax1.pie(
            percentage_d,
            #labels=labels_d,
            colors=colors_d,
            startangle=140,
            autopct='%1.1f%%',
            textprops={'family': 'sans-serif', 'fontsize': 12},
        )
        """
        ax1.set_title(
            "Καμμένες εκτάσεις - Χρήσεις γης Corine Land Cover 2018",
            fontdict={'family': 'sans-serif', 'fontsize': 20, 'fontweight': 'bold'},
            loc='center',
            pad=30
        )
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        """

        # Initialize a new list to store the updated labels
        updated_labels = []
        # Filter out labels from removed_labels that are already in labels_d
        # This ensures that only truly removed labels are appended to "Other"
        removed_labels = [label for label in removed_labels if label not in labels_d]
        # If the label is "Other", append it with the removed labels in parentheses
        # Otherwise, just add the label to the updated_labels list as is
        for label in labels_d:
            if label == "Other":
                # Append "Other" with removed labels in parentheses
                updated_labels.append(f"{label} ({''.join(removed_labels)})")
            else:
                updated_labels.append(label)
                #print(updated_labels)


        # Legend
        ax2 = fig.add_subplot(gs[1])
        patches = [
            plt.Line2D([0], [0], marker='o', color='w', label=label, markersize=10, markerfacecolor=color)
            for label, color in zip(updated_labels, colors_d)
        ]

        legend = ax2.legend(
            handles=patches,
            loc='lower right',
            fontsize=12,
            title="Land Use",
            shadow=False
        )

        legend.set_title("Land Use", prop={'size': '14', 'weight': 'bold'})
        ax2.axis('off')  # Turn off the axis

        # Set the title for the whole figure
        fig.suptitle(
            "Burned Areas - Corine Land Cover 2018",
            fontsize=20,
            fontweight='bold',
            family='sans-serif',
            y=0.95,  # Adjust this value to move the title up or down
        )
        # Save the figure
        file_name = os.path.basename(self.file_path).replace(".csv", "")
        plt.savefig(path_file + file_name + '_pie_chart.png', format='png', dpi=300, bbox_inches='tight')
        plt.show()

