"""
GUI for laser overview. No control. To be displayed at the laserlab entrance

:created: 2021-08-25

:author: Filip Lindau <filip.lindau@maxiv.lu.se>
"""

from PyQt5 import QtWidgets, QtCore, QtGui
import logging
import sys
import time
import random
sys.path.append('../TangoWidgetsQt5')
import striptool
from TangoDeviceClient import TangoDeviceClient
from ColorDefinitions import QTangoSizes, QTangoColors
from SliderCompositeWidgets import QTangoAttributeSlider
from SpectrumCompositeWidgets import QTangoReadAttributeSpectrum
from ButtonWidgets import QTangoCommandSelection
from LabelWidgets import QTangoStartLabel, QTangoAttributeUnitLabel, QTangoReadAttributeLabel
from LabelCompositeWidgets import QTangoReadAttributeBoolean, QTangoDeviceStatus, QTangoReadAttributeDouble
from EditWidgets import QTangoReadAttributeSpinBox, QTangoWriteAttributeSpinBox
from EditCompositeWidgets import QTangoWriteAttributeDouble
from LayoutWidgets import QTangoContentWidget

logger = logging.getLogger("TestSynchro")
formatter = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
# logger.propagate = False


class TestDeviceClient(TangoDeviceClient):
    """ Example device client using the test laser finesse and redpitaya5.

    """
    def __init__(self):
        TangoDeviceClient.__init__(self, "Lasers Overview", use_sidebar=False, use_bottombar=False, call_setup_layout=False)

        self.title_sizes = QTangoSizes()
        self.title_sizes.barHeight = 40
        self.top_spacing = 20
        self.setup_layout(False, False)
        self.attr_sizes.barHeight = 25
        self.attr_sizes.readAttributeHeight = 320
        self.attr_sizes.fontStretch = 80
        self.cont_sizes = QTangoSizes()
        self.cont_sizes.barHeight = 20
        self.cont_sizes.barWidth = 2
        self.cont_sizes.readAttributeWidth = 100
        self.cont_sizes.readAttributeHeight = 250
        self.cont_sizes.writeAttributeWidth = 299
        self.cont_sizes.fontStretch = 80
        self.cont_sizes.fontType = 'Arial'
        #        self.attr_sizes.fontType = 'Trebuchet MS'
        cont_colors = QTangoColors()
        cont_colors.primaryColor0 = cont_colors.secondaryColor0

        # Verdi setup
        #
        self.add_device("verdi", "astrella/oscillator/verdi")
        self.verdi_power_slider = QTangoAttributeSlider("Verdi P", self.attr_sizes, self.colors, show_write_widget=False, slider_style=4)
        self.verdi_power_slider.setSliderLimits(0, 6.5)
        self.add_attribute("power", "verdi", self.read_verdi_power, update_interval=0.3, single_shot=False,
                           get_info=True, attr_info_slot=self.verdi_power_slider.configureAttribute)

        self.verdi_status_label = QTangoDeviceStatus("Verdi", self.attr_sizes, self.colors)
        self.add_attribute("status", "verdi", self.verdi_status, update_interval=0.3, single_shot=False)
        self.add_attribute("state", "verdi", self.verdi_status, update_interval=0.3, single_shot=False)

        # Revolution setup
        #
        self.add_device("revolution", "astrella/regen/revolution")

        self.revolution_power_slider = QTangoAttributeSlider("Rev P", self.attr_sizes, self.colors, show_write_widget=False, slider_style=4)
        self.revolution_power_slider.setSliderLimits(0, 30)
        self.add_attribute("pd_power", "revolution", self.read_revolution_power, update_interval=0.3, single_shot=False,
                           get_info=True, attr_info_slot=self.revolution_power_slider.configureAttribute)

        self.revolution_status_label = QTangoDeviceStatus("Revolution", self.attr_sizes, self.colors)
        self.add_attribute("status", "revolution", self.revolution_status, update_interval=0.3, single_shot=False)
        self.add_attribute("state", "revolution", self.revolution_status, update_interval=0.3, single_shot=False)

        # Vitara setup
        #
        self.add_device("vitara", "astrella/oscillator/vitara")

        self.vitara_power_slider = QTangoAttributeSlider("Vitara P", self.attr_sizes, self.colors, show_write_widget=False, slider_style=4)
        self.vitara_power_slider.setSliderLimits(0, 700)
        self.add_attribute("pd_power", "vitara", self.read_vitara_power, update_interval=0.3, single_shot=False,
                           get_info=True, attr_info_slot=self.vitara_power_slider.configureAttribute)
        self.add_attribute("modelock_status", "vitara", self.read_vitara_modelock, update_interval=0.5, single_shot=False,
                           get_info=False)
        self.vitara_modelock_label = QTangoReadAttributeBoolean("Modelock", self.attr_sizes, self.colors)

        self.vitara_status_label = QTangoDeviceStatus("Vitara", self.attr_sizes, self.colors)
        self.add_attribute("status", "vitara", self.vitara_status, update_interval=0.3, single_shot=False)
        self.add_attribute("state", "vitara", self.vitara_status, update_interval=0.3, single_shot=False)

        # self.add_attribute("power", "vitara", self.read_vitara_power, update_interval=0.3, single_shot=False,
        #                    get_info=True, attr_info_slot=self.verdi_power_slider.configureAttribute)
        self.add_device("astrella_osc_spectrometer", "astrella/oscillator/spectrometer")
        self.vitara_l0_slider = QTangoAttributeSlider(u"Central \u03bb", self.attr_sizes, self.colors, show_write_widget=False, slider_style=4)
        self.vitara_l0_slider.setSliderLimits(700, 790)
        self.add_attribute("peakwavelength", "astrella_osc_spectrometer", self.read_astrella_l0, update_interval=0.3, single_shot=False,
                           get_info=True, attr_info_slot=self.vitara_l0_slider.configureAttribute)

        self.vitara_dl_slider = QTangoAttributeSlider("Bandwidth", self.attr_sizes, self.colors, show_write_widget=False, slider_style=4)
        self.vitara_dl_slider.setSliderLimits(0, 60)
        self.add_attribute("peakwidth", "astrella_osc_spectrometer", self.read_astrella_dl, update_interval=0.3, single_shot=False,
                           get_info=True, attr_info_slot=self.vitara_dl_slider.configureAttribute)


        # Synchrolock setup
        #
        self.add_device("slap", "astrella/oscillator/synchrolock")
        self.slap_status_label = QTangoDeviceStatus("Synchrolock", self.attr_sizes, self.colors)
        self.add_attribute("status", "slap", self.slap_status, update_interval=0.3, single_shot=False)
        self.add_attribute("state", "slap", self.slap_status, update_interval=0.3, single_shot=False)
        # Separate slap gui? There is quite a lot to adjust.
        self.slap_ferr_label = QTangoReadAttributeDouble("Error freq", self.attr_sizes, self.colors)
        self.add_attribute("error_frequency_abs", "slap", self.read_slap_ferr, update_interval=0.5, single_shot=False,
                           get_info=True, attr_info_slot=self.slap_ferr_label.configureAttribute)

        # Astrella setup
        #
        # Add energy device
        # Add Spectrometer device
        self.astrella_ir_energy_slider = QTangoAttributeSlider(u"IR Energy", self.attr_sizes, self.colors, show_write_widget=False, slider_style=4)
        self.astrella_ir_energy_slider.setSliderLimits(0, 11e-3)
        self.add_device("ir_energy", "testlaser/devices/redpitaya5")
        self.add_attribute("measurementdata1", "ir_energy", self.read_ir_energy, update_interval=0.3, single_shot=False,
                           get_info=True, attr_info_slot=self.astrella_ir_energy_slider.configureAttribute)

        # Astrella shutter setup
        self.add_device("shutter", "gunlaser/thg/shutter")
        self.shutter_status_label = QTangoDeviceStatus("Shutter", self.attr_sizes, self.colors)
        self.add_attribute("state", "shutter", self.shutter_status, update_interval=0.3, single_shot=False)
        self.add_attribute("status", "shutter", self.shutter_status, update_interval=0.3, single_shot=False)

        # THG setup
        #
        # Add energy device (same as astrella?)
        # Add spectrometer device

        # KMLabs setup
        #
        self.add_device("finesse", "gunlaser/oscillator/finesse")
        self.finesse_power_slider = QTangoAttributeSlider("Finesse P", self.attr_sizes, self.colors, show_write_widget=False, slider_style=4)
        self.finesse_power_slider.setSliderLimits(0, 6.5)
        self.add_attribute("power", "finesse", self.read_finesse_power, update_interval=0.3, single_shot=False,
                           get_info=True, attr_info_slot=self.finesse_power_slider.configureAttribute)

        self.finesse_status_label = QTangoDeviceStatus("Finesse", self.attr_sizes, self.colors)
        self.add_attribute("state", "finesse", self.finesse_status, update_interval=0.3, single_shot=False)
        self.add_attribute("status", "finesse", self.finesse_status, update_interval=0.3, single_shot=False)

        self.add_device("patara", "gunlaser/devices/patara")
        self.patara_status_label = QTangoDeviceStatus("Patara", self.attr_sizes, self.colors)
        self.add_attribute("state", "patara", self.patara_status, update_interval=0.3, single_shot=False)
        self.add_attribute("status", "patara", self.patara_status, update_interval=0.3, single_shot=False)

        self.add_device("redpitaya4", "gunlaser/devices/redpitaya4")
        self.patara_energy_slider = QTangoAttributeSlider("Patara J", self.attr_sizes, self.colors, show_write_widget=False, slider_style=4)
        self.patara_energy_slider.setSliderLimits(0, 50e-3)
        self.add_attribute("measurementdata2", "redpitaya4", self.read_patara_energy, update_interval=0.3, single_shot=False,
                           get_info=True, attr_info_slot=self.patara_energy_slider.configureAttribute)

        self.add_device("redpitaya1", "gunlaser/devices/redpitaya1")
        self.gunlaser_osc_power_slider = QTangoAttributeSlider("Osc P", self.attr_sizes, self.colors, show_write_widget=False, slider_style=4)
        self.gunlaser_osc_power_slider.setSliderLimits(0, 0.230)
        self.add_attribute("measurementdata1", "redpitaya1", self.read_gunlaser_osc_power, update_interval=0.3, single_shot=False,
                           get_info=True, attr_info_slot=self.gunlaser_osc_power_slider.configureAttribute)

        self.add_device("gunlaser_osc_spectrometer", "gunlaser/oscillator/spectrometer")
        self.gunlaser_l0_slider = QTangoAttributeSlider(u"Central \u03bb", self.attr_sizes, self.colors, show_write_widget=False, slider_style=4)
        self.gunlaser_l0_slider.setSliderLimits(720, 820)
        self.add_attribute("peakwavelength", "gunlaser_osc_spectrometer", self.read_gunlaser_l0, update_interval=0.3, single_shot=False,
                           get_info=True, attr_info_slot=self.gunlaser_l0_slider.configureAttribute)

        self.gunlaser_dl_slider = QTangoAttributeSlider("Bandwidth", self.attr_sizes, self.colors, show_write_widget=False, slider_style=4)
        self.gunlaser_dl_slider.setSliderLimits(0, 60)
        self.add_attribute("peakwidth", "gunlaser_osc_spectrometer", self.read_gunlaser_dl, update_interval=0.3, single_shot=False,
                           get_info=True, attr_info_slot=self.gunlaser_dl_slider.configureAttribute)

        self.add_device("halcyon", "gunlaser/oscillator/halcyon_raspberry")
        self.halcyon_modelock_label = QTangoReadAttributeBoolean("Modelock", self.attr_sizes, self.colors)
        self.add_attribute("modelocked", "halcyon", self.read_halcyon_modelock, update_interval=0.5, single_shot=False,
                           get_info=False)
        self.halcyon_ferr_label = QTangoReadAttributeDouble("Error freq", self.attr_sizes, self.colors)
        self.add_attribute("errorfrequency", "halcyon", self.read_halcyon_ferr, update_interval=0.5, single_shot=False,
                           get_info=False)
        self.halcyon_jitter_label = QTangoReadAttributeDouble("Jitter", self.attr_sizes, self.colors)
        self.add_attribute("jitter", "halcyon", self.read_halcyon_jitter, update_interval=0.5, single_shot=False,
                           get_info=False)

        self.add_device("cryo_regen", "gunlaser/regen/temperature")
        self.cryo_regen_label = QTangoReadAttributeDouble("Regen Temp", self.attr_sizes, self.colors)
        self.add_attribute("temperature", "cryo_regen", self.read_cryo_regen, update_interval=0.5, single_shot=False,
                           get_info=False)
        self.add_device("cryo_mp", "gunlaser/mp/temperature")
        self.cryo_mp_label = QTangoReadAttributeDouble("MP Temp", self.attr_sizes, self.colors)
        self.add_attribute("temperature", "cryo_mp", self.read_cryo_mp, update_interval=0.5, single_shot=False,
                           get_info=False)

        self.add_device("redpitaya2", "gunlaser/devices/redpitaya2")
        self.kmlabs_ir_energy_slider = QTangoAttributeSlider("IR Energy", self.attr_sizes, self.colors, show_write_widget=False, slider_style=4)
        self.kmlabs_ir_energy_slider.setSliderLimits(0, 11e-3)
        self.add_attribute("measurementdata2", "redpitaya2", self.read_kmlabs_ir_energy, update_interval=0.3, single_shot=False,
                           get_info=True, attr_info_slot=self.kmlabs_ir_energy_slider.configureAttribute)

        # self.add_attribute("ir_energy", "gunlaser_energy", self.read_gunlaser_energy, update_interval=0.3, single_shot=False,
        #                    get_info=True, attr_info_slot=self.gunlaser_energy_slider.configureAttribute)

        self.add_device("gunlaser_energy", "gunlaser/thg/energy")
        self.uv_energy_slider = QTangoAttributeSlider("UV Energy", self.attr_sizes, self.colors, show_write_widget=False, slider_style=4)
        self.uv_energy_slider.setSliderLimits(0, 170)
        self.add_attribute("uv_energy", "gunlaser_energy", self.read_uv_energy, update_interval=0.3, single_shot=False,
                           get_info=True, attr_info_slot=self.uv_energy_slider.configureAttribute)


        # Set up layout
        #
        self.astrella_layout = QTangoContentWidget("Astrella", horizontal=True, sizes=self.cont_sizes, colors=cont_colors)
        self.kmlabs_layout = QTangoContentWidget("KMLabs", horizontal=True, sizes=self.cont_sizes,
                                                   colors=cont_colors)
        # self.grid_layout = QtWidgets.QGridLayout()
        self.left_layout_0 = QtWidgets.QVBoxLayout()
        self.middle_layout_0 = QtWidgets.QHBoxLayout()
        self.right_layout_0 = QtWidgets.QVBoxLayout()
        self.left_layout_1 = QtWidgets.QVBoxLayout()
        self.middle_layout_1 = QtWidgets.QHBoxLayout()
        self.right_layout_1 = QtWidgets.QVBoxLayout()
        self.left_layout_0.setSpacing(16)
        self.left_layout_1.setSpacing(16)
        self.middle_layout_0.setSpacing(16)
        self.middle_layout_1.setSpacing(16)
        self.right_layout_0.setSpacing(16)
        self.right_layout_1.setSpacing(16)

        # self.add_layout(self.grid_layout)
        # self.grid_layout.setSpacing(16)
        # self.grid_layout.addLayout(self.left_layout_0, 0, 0)
        # self.grid_layout.addLayout(self.middle_layout_0, 0, 1)
        # self.grid_layout.addLayout(self.right_layout_0, 0, 2)
        # s_widget = QtWidgets.QWidget()
        # s_widget.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        # self.grid_layout.addWidget(s_widget, 1, 0)
        # self.grid_layout.addLayout(self.left_layout_1, 2, 0)
        # self.grid_layout.addLayout(self.middle_layout_1, 2, 1)
        # self.grid_layout.addLayout(self.right_layout_1, 2, 2)

        self.astrella_layout.addLayout(self.left_layout_0)
        self.astrella_layout.addLayout(self.middle_layout_0)
        self.astrella_layout.addLayout(self.right_layout_0)

        self.kmlabs_layout.addLayout(self.left_layout_1)
        self.kmlabs_layout.addLayout(self.middle_layout_1)
        self.kmlabs_layout.addLayout(self.right_layout_1)

        self.cont_layout = QtWidgets.QVBoxLayout()
        self.cont_layout.addWidget(self.astrella_layout)
        self.cont_layout.addWidget(self.kmlabs_layout)
        self.add_layout(self.cont_layout)

        self.left_layout_0.addWidget(self.verdi_status_label)
        self.left_layout_0.addWidget(self.revolution_status_label)
        self.left_layout_0.addWidget(self.vitara_status_label)
        self.left_layout_0.addWidget(self.slap_status_label)
        v_spacer_1 = QtWidgets.QSpacerItem(10, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.left_layout_0.addSpacerItem(v_spacer_1)

        h_spacer_1 = QtWidgets.QSpacerItem(30, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.middle_layout_0.addSpacerItem(h_spacer_1)
        self.middle_layout_0.addWidget(self.verdi_power_slider)
        self.middle_layout_0.addWidget(self.revolution_power_slider)
        h_spacer_6 = QtWidgets.QSpacerItem(50, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.middle_layout_0.addSpacerItem(h_spacer_6)
        self.middle_layout_0.addWidget(self.vitara_power_slider)
        self.middle_layout_0.addWidget(self.vitara_l0_slider)
        self.middle_layout_0.addWidget(self.vitara_dl_slider)
        self.middle_layout_0.addWidget(self.astrella_ir_energy_slider)
        h_spacer_7 = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.middle_layout_0.addSpacerItem(h_spacer_7)
        self.middle_layout_0.addWidget(self.uv_energy_slider)
        h_spacer_2 = QtWidgets.QSpacerItem(10, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.middle_layout_0.addSpacerItem(h_spacer_2)
        
        self.right_layout_0.addWidget(self.vitara_modelock_label)
        self.right_layout_0.addWidget(self.slap_ferr_label)
        self.right_layout_0.addWidget(self.shutter_status_label)
        v_spacer_r1 = QtWidgets.QSpacerItem(10, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.right_layout_0.addSpacerItem(v_spacer_r1)

        self.left_layout_1.addWidget(self.finesse_status_label)
        self.left_layout_1.addWidget(self.patara_status_label)
        v_spacer_2 = QtWidgets.QSpacerItem(10, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.left_layout_1.addSpacerItem(v_spacer_2)

        h_spacer_3 = QtWidgets.QSpacerItem(30, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.middle_layout_1.addSpacerItem(h_spacer_3)
        self.middle_layout_1.addWidget(self.finesse_power_slider)
        self.middle_layout_1.addWidget(self.patara_energy_slider)
        h_spacer_5 = QtWidgets.QSpacerItem(50, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.middle_layout_1.addSpacerItem(h_spacer_5)
        self.middle_layout_1.addWidget(self.gunlaser_osc_power_slider)
        self.middle_layout_1.addWidget(self.gunlaser_l0_slider)
        self.middle_layout_1.addWidget(self.gunlaser_dl_slider)
        self.middle_layout_1.addWidget(self.kmlabs_ir_energy_slider)
        h_spacer_4 = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.middle_layout_1.addSpacerItem(h_spacer_4)

        self.right_layout_1.addWidget(self.halcyon_modelock_label)
        self.right_layout_1.addWidget(self.halcyon_ferr_label)
        self.right_layout_1.addWidget(self.halcyon_jitter_label)
        v_spacer_r2 = QtWidgets.QSpacerItem(10, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.right_layout_1.addSpacerItem(v_spacer_r2)
        self.right_layout_1.addWidget(self.cryo_regen_label)
        self.right_layout_1.addWidget(self.cryo_mp_label)

        self.showFullScreen()
        self.update()

    def read_verdi_power(self, data):
        logger.debug("In read_verdi_power: {0}".format(data.value))
        self.verdi_power_slider.setAttributeValue(data)

    def verdi_status(self, data):
        widget = self.verdi_status_label
        if data.name == "Status":
            widget.setStatusText(data.value)
        else:
            widget.setState(data)

    def read_vitara_power(self, data):
        logger.debug("In read_vitara_power: {0}".format(data.value))
        self.vitara_power_slider.setAttributeValue(data)

    def read_vitara_modelock(self, data):
        logger.debug("In read_vitara_modelock: {0}".format(data.value))
        self.vitara_modelock_label.setAttributeValue(data)

    def vitara_status(self, data):
        widget = self.vitara_status_label
        if data.name == "Status":
            widget.setStatusText(data.value)
        else:
            widget.setState(data)

    def read_astrella_l0(self, data):
        self.vitara_l0_slider.setAttributeValue(data)

    def read_astrella_dl(self, data):
        self.vitara_dl_slider.setAttributeValue(data)

    def read_revolution_power(self, data):
        logger.debug("In read_revolution_power: {0}".format(data.value))
        self.revolution_power_slider.setAttributeValue(data)

    def revolution_status(self, data):
        if data.name == "Status":
            self.revolution_status_label.setStatusText(data.value)
        else:
            self.revolution_status_label.setState(data)

    def slap_status(self, data):
        if data.name == "Status":
            self.slap_status_label.setStatusText(data.value)
        else:
            self.slap_status_label.setState(data)

    def read_slap_ferr(self, data):
        self.slap_ferr_label.setAttributeValue(data)

    def shutter_status(self, data):
        if data.name == "Status":
            self.shutter_status_label.setStatusText(data.value)
        else:
            self.shutter_status_label.setState(data)

    def read_finesse_power(self, data):
        logger.debug("In read_finesse_power: {0}".format(data.value))
        self.finesse_power_slider.setAttributeValue(data)

    def finesse_status(self, data):
        widget = self.finesse_status_label
        if data.name == "Status":
            widget.setStatusText(data.value)
        else:
            widget.setState(data)

    def read_patara_energy(self, data):
        logger.debug("In read_patara_energy: {0}".format(data.value))
        self.patara_energy_slider.setAttributeValue(data)

    def patara_status(self, data):
        widget = self.patara_status_label
        if data.name == "Status":
            widget.setStatusText(data.value)
        else:
            widget.setState(data)

    def read_gunlaser_osc_power(self, data):
        self.gunlaser_osc_power_slider.setAttributeValue(data)

    def read_gunlaser_l0(self, data):
        self.gunlaser_l0_slider.setAttributeValue(data)

    def read_gunlaser_dl(self, data):
        self.gunlaser_dl_slider.setAttributeValue(data)

    def read_halcyon_modelock(self, data):
        self.halcyon_modelock_label.setAttributeValue(data)

    def read_halcyon_ferr(self, data):
        self.halcyon_ferr_label.setAttributeValue(data)

    def read_halcyon_jitter(self, data):
        self.halcyon_jitter_label.setAttributeValue(data)

    def read_cryo_regen(self, data):
        self.cryo_regen_label.setAttributeValue(data)

    def read_cryo_mp(self, data):
        self.cryo_mp_label.setAttributeValue(data)

    def read_gunlaser_energy(self, data):
        self.astrella_ir_energy_slider.setAttributeValue(data)

    def read_uv_energy(self, data):
        self.uv_energy_slider.setAttributeValue(data)

    def read_ir_energy(self, data):
        self.astrella_ir_energy_slider.setAttributeValue(data)

    def read_kmlabs_ir_energy(self, data):
        self.kmlabs_ir_energy_slider.setAttributeValue(data)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    pic_list = ["estrella2_rs.png", "estrella_beer_2.png", "estrella_damm.png"]
    random.seed(time.time_ns())
    splash_pix = QtGui.QPixmap(random.choice(pic_list))
    splash = QtWidgets.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())
    font = splash.font()
    font.setPixelSize(12)
    font.setWeight(QtGui.QFont.Bold)
    splash.setFont(font)
    splash.show()
    splash.showMessage('Importing modules', alignment=int(QtCore.Qt.AlignBottom) | int(QtCore.Qt.AlignHCenter),
                       color=QtGui.QColor('#63120c'))
    app.processEvents()

    splash.showMessage('Starting GUI\n\n\n', alignment=int(QtCore.Qt.AlignBottom) | int(QtCore.Qt.AlignHCenter),
                       color=QtGui.QColor('#000000'))
    app.processEvents()
    myapp = TestDeviceClient()
    myapp.show()
    splash.finish(myapp)
    app.setWindowIcon(QtGui.QIcon("estrella_beer_2.png"))
    sys.exit(app.exec_())
