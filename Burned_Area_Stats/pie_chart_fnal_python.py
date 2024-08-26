# Δημιουργία διαγράμματος pie chart για την απεικόνηση ποσοστών ανα χρήση γης μιας καμμένης περιοχής

# Εισαγωγή βιβλιωθηκών
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from matplotlib.gridspec import GridSpec

class PlotCLC:
    def __init__(self, CorineLandCover_PATH):
        self.file_path = CorineLandCover_PATH  # Αλλάξτε τη διαδρομή στο αρχείο σας

        self.CLC_number_to_legend_color = {
            111: ("#e6004d", "Continuous urban fabric"),
            112: ("#ff0000", "Discontinuous urban fabric"),
            121: ("#cc4df2", "Industrial or commercial units"),
            122: ("#cc0000", "Road and rail networks and associated land"),
            123: ("#e6004d", "Port areas"),
            124: ("#e6cce6", "Airports"),
            131: ("#a600cc", "Mineral extraction sites"),
            132: ("#a64d00", "Dump sites"),
            133: ("#ff4dff", "Construction sites"),
            141: ("#ffa6ff", "Green urban areas"),
            142: ("#ffe6ff", "Sport and leisure facilities"),
            211: ("#ffffa8", "Non-irrigated arable land"),
            212: ("#ffff00", "Permanently irrigated land"),
            213: ("#e6e600", "Rice fields"),
            221: ("#e68000", "Vineyards"),
            222: ("#f2a64d", "Fruit trees and berry plantations"),
            223: ("#e6a600", "Olive groves"),
            231: ("#e6e64d", "Pastures"),
            241: ("#ffe6a6", "Annual crops associated with permanent crops"),
            242: ("#ffe64d", "Complex cultivation patterns"),
            243: ("#e6cc4d", "Land principally occupied by agriculture,\nwith significant areas of natural vegetation"),
            244: ("#e6cc4d", "Agro-forestry areas"),
            311: ("#80ff00", "Broad-leaved forest"),
            312: ("#00a600", "Coniferous forest"),
            313: ("#4dff00", "Mixed forest"),
            321: ("#ccf24d", "Natural grasslands"),
            322: ("#a6ff80", "Moors and heathland"),
            323: ("#a6e64d", "Sclerophyllous vegetation"),
            324: ("#a6f200", "Transitional woodland-shrub"),
            331: ("#e6e6e6", "Beaches, dunes, sands"),
            332: ("#cccccc", "Bare rocks"),
            333: ("#ccffcc", "Sparsely vegetated areas"),
            334: ("#000000", "Burnt areas"),
            335: ("#a6e6cc", "Glaciers and perpetual snow"),
            411: ("#a6a6ff", "Inland marshes"),
            412: ("#4d4dff", "Peat bogs"),
            421: ("#ccccff", "Salt marshes"),
            422: ("#e6e6ff", "Salines"),
            423: ("#a6a6e6", "Intertidal flats"),
            511: ("#00ccf2", "Water courses"),
            512: ("#80f2e6", "Water bodies"),
            521: ("#00ffa6", "Coastal lagoons"),
            522: ("#00ffa6", "Estuaries"),
            523: ("#e6f2ff", "Sea and ocean"),
            000: ("#a4a4a6", "Other")
        }

        # make the CorinaLandCover Plot
        self.MakePlot(self.file_path)

    def MakePlot(self, file_path):
        # Λεξικό με τις κατηγορίες του Corine Land Cover
        # Δημιουργία ενός λεξικού που αντιστοιχίζει αριθμούς με χρώματα σε μορφή HEX
        # Κωδικός , Χρώμα, Όνομα κατηγορίας

        code, percentage, colors, labels = self.read_csv_and_prepare_data(self.file_path)
        print(f"Οι κωδικοί είναι: {code} \n"
              f"Τα ποσοστά είναι: {percentage} \n"
              f"Τα χρώματα είναι: {colors} \n"
              f"Οι κατηγορίες είναι: {labels}")

        #self.pie_chart(percentage, colors, labels, os.path.basename(file_path).replace(".csv", ".png"))
        #self.create_legend(labels, colors)
        self.combined_pie_and_legend(percentage, colors, labels, os.path.basename(file_path).replace(".csv", ".png"))

        self.pie_chart(percentage, colors, labels, os.path.basename(file_path).replace(".csv", "_pie.png"))

    # Συνάρτηση get_color_and_category
    # Εισάγωντας τον κωδικό μιας κατηγορίας του CLC επιστρέφει το χρώμα της και το ονομά της

    # Συνάρτηση που επιστρέφει το χρώμα που αντιστοιχεί σε έναν αριθμό
    def get_color_and_category(self, code):
        if code in self.CLC_number_to_legend_color:
            color, category = self.CLC_number_to_legend_color[code]
            return color, category
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
        for i in range(len(data_frame["Percentage"])):
            if data_frame["Percentage"][i] < 0.03:
                percentage_sum += data_frame["Percentage"][i]
                to_remove.append(i)
        # Αφαίρεση των γραμμών που έχουν μικρό ποσοστό
        data_frame = data_frame.drop(to_remove)

        # Προσθήκη γραμμής για το σύνολο των μικρών ποσοστών
        if percentage_sum > 0:
            additional_row = pd.DataFrame({"Code": [000], "Percentage": [percentage_sum]})
            data_frame = pd.concat([data_frame, additional_row], ignore_index=True)

        # Επιστροφή του επεξεργασμένου DataFrame
        print(f"Τελικό:\n{data_frame}\n")
        return data_frame  # Επιστροφή του επεξεργασμένου DataFrame


    # Συνάρτηση για την εισαγωγή δεδομένων απεικόνισης


    def read_csv_and_prepare_data(self, file_path):
        # Διαβάζουμε τα δεδομένα από το CSV αρχείο
        data_frame = pd.read_csv(file_path, header=None, names=["Code", "Percentage"])
        data_frame['Percentage'] = data_frame['Percentage'] / 100

        data_frame_checked = self.data_frame_check(data_frame)

        # Δημιουργία λιστών για τους κωδικούς και τα ποσοστά
        code = data_frame_checked["Code"].tolist()
        percentage = data_frame_checked["Percentage"].tolist()
        colors = []
        labels = []

        # Λήψη χρωμάτων και ετικετών για κάθε κωδικό
        for number in code:
            color, description = self.get_color_and_category(number)
            if color and description:
                labels.append(description)
                colors.append(color)

        return code, percentage, colors, labels



    # Συνάρτηση δημιούργιας διαγράμματος πίτας


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

    def combined_pie_and_legend(self, percentage_d, colors_d, labels_d, path_file):
        fig = plt.figure(figsize=(10, 10))  # Adjusted to give more width for the legend
        gs = GridSpec(1, 2, width_ratios=[2, 0.5])  # 1 row, 2 columns; first column 2 times wider than the second

        # Pie chart
        ax1 = fig.add_subplot(gs[0])
        ax1.pie(
            percentage_d,
            labels=labels_d,
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
        # Legend
        ax2 = fig.add_subplot(gs[1])
        patches = [
            plt.Line2D([0], [0], marker='o', color='w', label=label, markersize=10, markerfacecolor=color)
            for label, color in zip(labels_d, colors_d)
        ]
        legend = ax2.legend(
            handles=patches,
            loc='lower right',
            fontsize=12,
            title="Κατηγορίες Χρήσης Γης",
            shadow=False
        )

        legend.set_title("Κατηγορίες Χρήσης Γης", prop={'size': '14', 'weight': 'bold'})
        ax2.axis('off')  # Turn off the axis

        # Set the title for the whole figure
        fig.suptitle(
            "Καμμένες εκτάσεις - Χρήσεις γης Corine Land Cover 2018",
            fontsize=20,
            fontweight='bold',
            family='sans-serif',
            y=0.95  # Adjust this value to move the title up or down
        )
        # Save the figure
        plt.savefig(path_file + 'pie_chart', format='png', bbox_inches='tight')
        plt.show()

