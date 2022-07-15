"""
GUI for basic Astrella functionality control

:created: 2021-08-20

:author: Filip Lindau <filip.lindau@maxiv.lu.se>
"""

from PyQt5 import QtWidgets, QtCore, QtGui
import logging
import sys
import time
import random
import ctypes
sys.path.append('../TangoWidgetsQt5')
import striptool
from TangoDeviceClient import TangoDeviceClient
from ColorDefinitions import QTangoSizes
from SliderCompositeWidgets import QTangoAttributeSlider
from SpectrumCompositeWidgets import QTangoReadAttributeSpectrum
from ButtonWidgets import QTangoCommandSelection
from LabelWidgets import QTangoStartLabel, QTangoAttributeUnitLabel, QTangoReadAttributeLabel
from LabelCompositeWidgets import QTangoDeviceNameStatus, QTangoReadAttributeBoolean, QTangoReadAttributeDouble
from EditWidgets import QTangoReadAttributeSpinBox, QTangoWriteAttributeSpinBox
from EditCompositeWidgets import QTangoWriteAttributeDouble

logger = logging.getLogger("Astrella")
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
        TangoDeviceClient.__init__(self, "Astrella Overview", use_sidebar=False, use_bottombar=False, call_setup_layout=False)

        self.logger.setLevel(logging.INFO)

        self.fund_enabled_data = False
        self.harm_enabled_data = False
        self.wavelengths = None

        self.title_sizes = QTangoSizes()
        self.title_sizes.barHeight = 30
        self.top_spacing = 20
        self.setup_layout(False, False)
        self.attr_sizes.barHeight = 15
        self.attr_sizes.readAttributeHeight = 170
        self.attr_sizes.fontStretch = 100

        # Verdi setup
        #
        self.add_device("verdi", "astrella/oscillator/verdi")

        self.verdi_power_slider = QTangoAttributeSlider("Verdi Power", self.attr_sizes, self.colors, show_write_widget=True, slider_style=4)
        self.verdi_power_slider.setSliderLimits(0, 6.5)
        self.verdi_power_slider.newWriteValueSignal.connect(self.write_verdi_power)

        self.add_attribute("power", "verdi", self.read_verdi_power, update_interval=0.3, single_shot=False,
                           get_info=True, attr_info_slot=self.verdi_power_slider.configureAttribute)

        self.verdi_temperature_slider = QTangoAttributeSlider("Verdi Temp", self.attr_sizes, self.colors, show_write_widget=False,
                                                              slider_style=4)
        self.verdi_temperature_slider.setSliderLimits(10, 25)
        self.add_attribute("temperature_main", "verdi", self.read_verdi_temperature, update_interval=0.5, single_shot=False,
                           get_info=True, attr_info_slot=self.verdi_temperature_slider.configureAttribute)

        self.verdi_current_slider = QTangoAttributeSlider("Verdi Current", self.attr_sizes, self.colors, show_write_widget=False,
                                                              slider_style=4)
        self.verdi_current_slider.setSliderLimits(0, 40)
        self.add_attribute("diode_current", "verdi", self.read_verdi_current, update_interval=0.5, single_shot=False,
                           get_info=True, attr_info_slot=self.verdi_current_slider.configureAttribute)

        self.verdi_commands = QTangoCommandSelection("Verdi", self.attr_sizes, self.colors)
        self.verdi_commands.addCmdButton("On", self.verdi_enable)
        self.verdi_commands.addCmdButton("Off", self.verdi_disable)
        self.verdi_commands.addCmdButton("Open", self.verdi_open)
        self.verdi_commands.addCmdButton("Close", self.verdi_close)
        self.add_attribute("state", "verdi", self.verdi_status, update_interval=0.3, single_shot=False)

        # Revolution setup
        #
        self.add_device("revolution", "astrella/regen/revolution")

        self.revolution_power_slider = QTangoAttributeSlider("Rev Power", self.attr_sizes, self.colors, show_write_widget=False, slider_style=4)
        self.revolution_power_slider.setSliderLimits(0, 30)
        self.add_attribute("pd_power", "revolution", self.read_revolution_power, update_interval=0.3, single_shot=False,
                           get_info=True, attr_info_slot=self.revolution_power_slider.configureAttribute)

        self.revolution_temp_slider = QTangoAttributeSlider("Rev Temp", self.attr_sizes, self.colors, show_write_widget=False,
                                                            slider_style=4)
        self.revolution_temp_slider.setSliderLimits(160, 250)
        self.add_attribute("head_temp", "revolution", self.read_revolution_temp, update_interval=0.5, single_shot=False,
                           get_info=True, attr_info_slot=self.revolution_temp_slider.configureAttribute)

        self.revolution_current_slider = QTangoAttributeSlider("Rev Current", self.attr_sizes, self.colors, show_write_widget=False,
                                                               slider_style=4)
        self.revolution_current_slider.setSliderLimits(0, 20)
        self.revolution_current_slider.newWriteValueSignal.connect(self.write_revolution_current)
        self.add_attribute("diode_current_actual", "revolution", self.read_revolution_current, update_interval=0.5, single_shot=False,
                           get_info=True, attr_info_slot=self.revolution_current_slider.configureAttribute)

        self.revolution_commands = QTangoCommandSelection("Revolution", self.attr_sizes, self.colors)
        self.revolution_commands.addCmdButton("On", self.revolution_on)
        self.revolution_commands.addCmdButton("Off", self.revolution_off)
        self.revolution_commands.addCmdButton("Go OP", self.revolution_operating)
        self.add_attribute("state", "revolution", self.revolution_status, update_interval=0.3, single_shot=False)

        # Vitara setup
        #
        self.add_device("vitara", "astrella/oscillator/vitara")

        self.vitara_power_slider = QTangoAttributeSlider("Vitara Power", self.attr_sizes, self.colors, show_write_widget=False, slider_style=4)
        self.vitara_power_slider.setSliderLimits(0, 700)
        self.add_attribute("pd_power", "vitara", self.read_vitara_power, update_interval=0.3, single_shot=False,
                           get_info=True, attr_info_slot=self.vitara_power_slider.configureAttribute)
        self.add_attribute("modelock_status", "vitara", self.read_vitara_modelock, update_interval=0.5, single_shot=False,
                           get_info=False)
        self.vitara_modelock_label = QTangoReadAttributeBoolean("Modelock", self.attr_sizes, self.colors)
        self.vitara_rasterizing_label = QTangoReadAttributeBoolean("Rasterizing", self.attr_sizes, self.colors)
        self.add_attribute("rasterizing_status", "vitara", self.read_vitara_rasterizing, update_interval=1.0, single_shot=False,
                           get_info=False)

        self.vitara_commands = QTangoCommandSelection("Vitara", self.attr_sizes, self.colors)
        self.vitara_commands.addCmdButton("Go OP", self.vitara_goto_operating)
        self.vitara_commands.addCmdButton("Go KS", self.vitara_goto_kickstart)
        self.vitara_commands.addCmdButton("Starter", self.vitara_start_starter)
        # self.vitara_commands.addCmdButton("Stop starter", self.vitara_stop_starter)
        self.add_attribute("state", "vitara", self.vitara_status, update_interval=0.3, single_shot=False)

        # self.add_attribute("power", "vitara", self.read_vitara_power, update_interval=0.3, single_shot=False,
        #                    get_info=True, attr_info_slot=self.verdi_power_slider.configureAttribute)
        self.add_device("oscillator_spectrometer", "astrella/oscillator/spectrometer")
        self.vitara_l0_slider = QTangoAttributeSlider(u"Central \u03bb", self.attr_sizes, self.colors, show_write_widget=False, slider_style=4)
        self.vitara_l0_slider.setSliderLimits(700, 790)
        self.add_attribute("peakwavelength", "oscillator_spectrometer", self.read_peakwavelength, update_interval=0.5, single_shot=False,
                           get_info=True, attr_info_slot=self.vitara_l0_slider.configureAttribute)

        self.vitara_dl_slider = QTangoAttributeSlider("Bandwidth", self.attr_sizes, self.colors, show_write_widget=False, slider_style=4)
        self.vitara_dl_slider.setSliderLimits(0, 60)
        self.add_attribute("peakwidth", "oscillator_spectrometer", self.read_peakwidth, update_interval=0.5, single_shot=False,
                           get_info=True, attr_info_slot=self.vitara_dl_slider.configureAttribute)

        self.vitara_spectrum = QTangoReadAttributeSpectrum("Bandwidth", self.attr_sizes, self.colors)
        self.vitara_spectrum.setXRange(700, 850)
        self.add_attribute("spectrum", "oscillator_spectrometer", self.read_spectrum, update_interval=0.5,
                           single_shot=False, get_info=True, attr_info_slot=self.vitara_spectrum.configureAttribute)
        self.add_attribute("wavelengths", "oscillator_spectrometer", self.read_wavelengths, update_interval=0.5,
                           single_shot=True, get_info=False)

        # SDG setup
        #
        self.add_device("sdg", "astrella/regen/sdg")
        self.sdg_commands = QTangoCommandSelection("Delay generator", self.attr_sizes, self.colors)
        self.sdg_commands.addCmdButton("Reset", self.sdg_reset)
        self.add_attribute("state", "sdg", self.sdg_status, update_interval=0.3, single_shot=False)

        # Synchrolock setup
        #
        self.add_device("slap", "astrella/oscillator/synchrolock")
        self.slap_commands = QTangoCommandSelection("Synchrolock", self.attr_sizes, self.colors)
        self.slap_commands.addCmdButton("Init", self.slap_init)
        self.slap_commands.addCmdButton("Fund", self.slap_fund)
        self.slap_commands.addCmdButton("Harm", self.slap_harm)
        self.add_attribute("state", "slap", self.slap_status, update_interval=0.3, single_shot=False)
        # Separate slap gui? There is quite a lot to adjust.
        self.slap_fund_enabled_label = QTangoReadAttributeBoolean("Fund enabled", self.attr_sizes, self.colors)
        self.add_attribute("fund_enabled", "slap", self.read_slap_fund_enabled, update_interval=0.5, single_shot=False,
                           get_info=False)
        self.slap_harm_enabled_label = QTangoReadAttributeBoolean("Harm enabled", self.attr_sizes, self.colors)
        self.add_attribute("harm_enabled", "slap", self.read_slap_harm_enabled, update_interval=0.5, single_shot=False,
                           get_info=False)
        self.slap_ferr_label = QTangoReadAttributeDouble("Error freq", self.attr_sizes, self.colors)
        self.add_attribute("error_frequency_abs", "slap", self.read_slap_ferr, update_interval=0.5, single_shot=False,
                           get_info=True, attr_info_slot=self.slap_ferr_label.configureAttribute)
        self.slap_ferr_label.valueSpinbox.setDataFormat("%d")

        self.slap_fund_error_slider = QTangoAttributeSlider("Fund error", self.attr_sizes, self.colors, show_write_widget=False, slider_style=4)
        self.slap_fund_error_slider.setSliderLimits(-5, 5)
        self.add_attribute("fund_phase_error", "slap", self.read_slap_fund_err, update_interval=0.5, single_shot=False,
                           get_info=True, attr_info_slot=self.slap_fund_error_slider.configureAttribute)
        self.slap_harm_error_slider = QTangoAttributeSlider("Harm error", self.attr_sizes, self.colors, show_write_widget=False, slider_style=4)
        self.slap_harm_error_slider.setSliderLimits(-5, 5)
        self.add_attribute("harm_phase_error", "slap", self.read_slap_harm_err, update_interval=0.5, single_shot=False,
                           get_info=True, attr_info_slot=self.slap_harm_error_slider.configureAttribute)
        self.slap_picomotor_edit = QTangoWriteAttributeDouble("Picomotor", self.attr_sizes, self.colors)
        self.add_attribute("picomotor_pos", "slap", self.read_slap_picomotor, update_interval=0.5, single_shot=False,
                           get_info=True, attr_info_slot=self.slap_picomotor_edit.configureAttribute)
        self.slap_picomotor_edit.writeValueLineEdit.newValueSignal.connect(self.write_slap_picomotor)
        self.slap_picomotor_edit.valueSpinbox.setDataFormat("%d")
        self.slap_picomotor_edit.writeValueLineEdit.setDataFormat("%d")
        self.slap_fund_phase_edit = QTangoWriteAttributeDouble("Fund phase", self.attr_sizes, self.colors)
        self.slap_fund_phase_edit.writeValueLineEdit.newValueSignal.connect(self.write_slap_fund_phase)
        self.slap_fund_phase_edit.valueSpinbox.setDataFormat("%d")
        self.slap_fund_phase_edit.writeValueLineEdit.setDataFormat("%d")
        self.add_attribute("fund_phase_shift", "slap", self.read_slap_fund_phase, update_interval=0.5, single_shot=False,
                           get_info=True, attr_info_slot=self.slap_fund_phase_edit.configureAttribute)
        self.slap_harm_phase_edit = QTangoWriteAttributeDouble("Harm phase", self.attr_sizes, self.colors)
        self.slap_harm_phase_edit.writeValueLineEdit.newValueSignal.connect(self.write_slap_harm_phase)
        self.slap_harm_phase_edit.valueSpinbox.setDataFormat("%d")
        self.slap_harm_phase_edit.writeValueLineEdit.setDataFormat("%d")
        self.add_attribute("harm_phase_shift", "slap", self.read_slap_harm_phase, update_interval=0.5, single_shot=False,
                           get_info=True, attr_info_slot=self.slap_harm_phase_edit.configureAttribute)


        # Astrella setup
        #
        # Add energy device
        # Add Spectrometer device
        self.ir_energy_slider = QTangoAttributeSlider(u"IR Energy", self.attr_sizes, self.colors, show_write_widget=False, slider_style=4)
        self.ir_energy_slider.setSliderLimits(0, 11)

        # THG setup
        #
        # Add energy device (same as astrella?)
        # Add spectrometer device
        self.add_device("uv_energy", "gunlaser/thg/energy")
        self.uv_energy_slider = QTangoAttributeSlider(u"UV Energy", self.attr_sizes, self.colors, show_write_widget=False, slider_style=4)
        self.uv_energy_slider.setSliderLimits(0, 170)
        self.add_attribute("uv_energy", "uv_energy", self.read_uv_energy, update_interval=0.3, single_shot=False,
                           get_info=True, attr_info_slot=self.uv_energy_slider.configureAttribute)

        # Shutter
        self.add_device("shutter", "gunlaser/thg/shutter")
        self.shutter_commands = QTangoCommandSelection("Shutter", self.attr_sizes, self.colors)
        self.shutter_commands.addCmdButton("Open", self.shutter_open)
        self.shutter_commands.addCmdButton("Close", self.shutter_close)
        self.add_attribute("state", "shutter", self.shutter_status, update_interval=0.3, single_shot=False)

        # Set up layout
        #
        self.grid_layout = QtWidgets.QGridLayout()
        self.left_layout_0 = QtWidgets.QVBoxLayout()
        self.right_layout_0 = QtWidgets.QHBoxLayout()
        self.left_layout_1 = QtWidgets.QVBoxLayout()
        self.right_layout_1 = QtWidgets.QHBoxLayout()
        self.left_layout_2 = QtWidgets.QVBoxLayout()
        self.right_layout_2 = QtWidgets.QHBoxLayout()
        self.left_layout_0.setSpacing(16)
        self.left_layout_1.setSpacing(16)
        self.left_layout_2.setSpacing(16)
        self.synchro_layout_2 = QtWidgets.QVBoxLayout()
        self.synchro_layout_2.setSpacing(16)
        self.right_layout_2.addLayout(self.synchro_layout_2)
        self.right_layout_2.setContentsMargins(6, 0, 6, 0)

        self.add_layout(self.grid_layout)
        self.grid_layout.setSpacing(12)
        self.grid_layout.addLayout(self.left_layout_0, 0, 0)
        self.grid_layout.addLayout(self.right_layout_0, 0, 1)
        s_widget = QtWidgets.QWidget()
        s_widget.setMinimumSize(0, 0)
        s_widget.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.grid_layout.addWidget(s_widget, 1, 0)
        self.grid_layout.addLayout(self.left_layout_1, 2, 0)
        self.grid_layout.addLayout(self.right_layout_1, 2, 1)
        s_widget2 = QtWidgets.QWidget()
        s_widget2.setMinimumSize(0, 0)
        s_widget2.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.grid_layout.addWidget(s_widget2, 3, 0)
        self.grid_layout.addLayout(self.left_layout_2, 4, 0)
        self.grid_layout.addLayout(self.right_layout_2, 4, 1)

        # h_spacer_4 = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        # self.add_spaceritem(h_spacer_4)
        # self.add_layout(self.right_layout)

        self.left_layout_0.addWidget(self.verdi_commands)
        self.left_layout_0.addWidget(self.revolution_commands)
        self.left_layout_0.addWidget(self.sdg_commands)
        v_spacer_1 = QtWidgets.QSpacerItem(10, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.left_layout_0.addSpacerItem(v_spacer_1)
        # lay_verdi_sliders = QtWidgets.QHBoxLayout()
        self.right_layout_0.addWidget(self.verdi_power_slider)
        self.right_layout_0.addWidget(self.verdi_current_slider)
        self.right_layout_0.addWidget(self.verdi_temperature_slider)
        h_spacer_1 = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.right_layout_0.addSpacerItem(h_spacer_1)
        # self.left_layout.addLayout(lay_verdi_sliders)
        # lay_rev_sliders = QtWidgets.QHBoxLayout()
        self.right_layout_0.addWidget(self.revolution_power_slider)
        self.right_layout_0.addWidget(self.revolution_current_slider)
        self.right_layout_0.addWidget(self.revolution_temp_slider)
        h_spacer_2 = QtWidgets.QSpacerItem(10, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        # lay_rev_sliders.addSpacerItem(h_spacer_2)
        # self.left_layout.addLayout(lay_rev_sliders)

        self.left_layout_1.addWidget(self.vitara_commands)
        self.left_layout_1.addWidget(self.vitara_rasterizing_label)
        self.left_layout_1.addWidget(self.vitara_modelock_label)
        self.left_layout_1.addWidget(self.slap_commands)
        v_spacer_2 = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.left_layout_1.addSpacerItem(v_spacer_2)
        # lay_vitara_sliders = QtWidgets.QHBoxLayout()
        self.right_layout_1.addWidget(self.vitara_power_slider)
        self.right_layout_1.addWidget(self.vitara_l0_slider)
        self.right_layout_1.addWidget(self.vitara_dl_slider)
        self.right_layout_1.addWidget(self.vitara_spectrum)
        h_spacer_2 = QtWidgets.QSpacerItem(10, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.right_layout_1.addSpacerItem(h_spacer_2)
        self.right_layout_1.addWidget(self.ir_energy_slider)
        self.right_layout_1.addWidget(self.uv_energy_slider)
        # self.right_layout.addLayout(lay_vitara_sliders)

        self.left_layout_2.addWidget(self.slap_commands)
        self.left_layout_2.addWidget(self.slap_fund_enabled_label)
        self.left_layout_2.addWidget(self.slap_harm_enabled_label)
        v_spacer_3 = QtWidgets.QSpacerItem(10, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.left_layout_2.addSpacerItem(v_spacer_3)
        self.left_layout_2.addWidget(self.shutter_commands)

        # self.right_layout_2.addWidget(self.slap_ferr_slider)
        h_spacer_3 = QtWidgets.QSpacerItem(10, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.right_layout_2.addSpacerItem(h_spacer_3)
        self.right_layout_2.addWidget(self.slap_fund_error_slider)
        self.right_layout_2.addWidget(self.slap_harm_error_slider)
        # self.right_layout_2.addWidget(self.slap_fund_phase_edit)
        # self.right_layout_2.addWidget(self.slap_harm_phase_slider)

        self.synchro_layout_2.addWidget(self.slap_ferr_label)
        self.synchro_layout_2.addWidget(self.slap_picomotor_edit)
        v_spacer_4 = QtWidgets.QSpacerItem(10, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.synchro_layout_2.addSpacerItem(v_spacer_4)
        self.synchro_layout_2.addWidget(self.slap_fund_phase_edit)
        self.synchro_layout_2.addWidget(self.slap_harm_phase_edit)

    def read_verdi_power(self, data):
        logger.debug("In read_verdi_power: {0}".format(data.value))
        self.verdi_power_slider.setAttributeValue(data)

    def read_verdi_temperature(self, data):
        logger.debug("In read_verdi_temperature: {0}".format(data.value))
        self.verdi_temperature_slider.setAttributeValue(data)

    def read_verdi_current(self, data):
        logger.debug("In read_verdi_current: {0}".format(data.value))
        self.verdi_current_slider.setAttributeValue(data)

    def write_verdi_power(self):
        new_power = self.verdi_power_slider.getWriteValue()
        logger.debug("In write_power: new value {0}".format(new_power))
        self.attributes["power_verdi"].attr_write(new_power)

    def verdi_enable(self):
        self.devices["verdi"].command_inout_asynch("laser_enable", None, True)

    def verdi_disable(self):
        self.devices["verdi"].command_inout_asynch("laser_disable", None, True)

    def verdi_open(self):
        self.devices["verdi"].command_inout_asynch("laser_enable", None, True)

    def verdi_close(self):
        self.devices["verdi"].command_inout_asynch("laser_disable", None, True)

    def verdi_status(self, data):
        self.verdi_commands.setStatus(data, data.value)

    def read_vitara_power(self, data):
        logger.debug("In read_vitara_power: {0}".format(data.value))
        self.vitara_power_slider.setAttributeValue(data)

    def read_vitara_modelock(self, data):
        logger.debug("In read_vitara_modelock: {0}".format(data.value))
        self.vitara_modelock_label.setAttributeValue(data)

    def read_vitara_rasterizing(self, data):
        self.vitara_rasterizing_label.setAttributeValue(data)

    def vitara_status(self, data):
        self.vitara_commands.setStatus(data, data.value)

    def vitara_goto_operating(self):
        self.devices["vitara"].command_inout_asynch("goto_operating_pos", None, True)

    def vitara_goto_kickstart(self):
        self.devices["vitara"].command_inout_asynch("goto_kickstart_pos", None, True)

    def vitara_start_starter(self):
        self.devices["vitara"].command_inout_asynch("starter_on", None, True)

    def vitara_stop_starter(self):
        self.devices["vitara"].command_inout_asynch("starter_off", None, True)

    def read_revolution_power(self, data):
        logger.debug("In read_revolution_power: {0}".format(data.value))
        self.revolution_power_slider.setAttributeValue(data)

    def read_revolution_current(self, data):
        logger.debug("In read_revolution_current: {0}".format(data.value))
        self.revolution_current_slider.setAttributeValue(data)

    def write_revolution_current(self):
        new_value = self.revolution_current_slider.getWriteValue()
        logger.debug("In write_revolution_current: new value {0}".format(new_value))
        self.attributes["diode_current_revolution"].attr_write(new_value)

    def read_revolution_temp(self, data):
        logger.debug("In read_revolution_temp: {0}".format(data.value))
        self.revolution_temp_slider.setAttributeValue(data)

    def revolution_on(self):
        self.devices["revolution"].command_inout_asynch("on", None, True)

    def revolution_off(self):
        self.devices["revolution"].command_inout_asynch("off", None, True)

    def revolution_operating(self):
        self.devices["revolution"].command_inout_asynch("set_operating", None, True)

    def revolution_status(self, data):
        self.revolution_commands.setStatus(data, data.value)

    def sdg_reset(self):
        self.devices["sdg"].command_inout_asynch("reset", None, True)

    def sdg_status(self, data):
        self.sdg_commands.setStatus(data, data.value)

    def slap_init(self):
        self.devices["slap"].command_inout_asynch("init", None, True)

    def slap_fund(self):
        if self.fund_enabled_data:
            self.devices["slap"].write_attribute("fund_enabled", False)
        else:
            self.devices["slap"].write_attribute("fund_enabled", True)

    def slap_harm(self):
        if self.harm_enabled_data:
            self.devices["slap"].write_attribute("harm_enabled", False)
        else:
            self.devices["slap"].write_attribute("harm_enabled", True)

    def slap_status(self, data):
        self.slap_commands.setStatus(data, data.value)

    def read_slap_fund_enabled(self, data):
        self.slap_fund_enabled_label.setAttributeValue(data)
        self.fund_enabled_data = data.value
        if data.value:
            self.slap_commands.setButtonText("Fund", "Fund disable")
        else:
            self.slap_commands.setButtonText("Fund", "Fund enable")

    def read_slap_harm_enabled(self, data):
        self.slap_harm_enabled_label.setAttributeValue(data)
        self.harm_enabled_data = data.value
        if data.value:
            self.slap_commands.setButtonText("Harm", "Harm disable")
        else:
            self.slap_commands.setButtonText("Harm", "Harm enable")

    def read_slap_ferr(self, data):
        self.slap_ferr_label.setAttributeValue(data)

    def read_slap_fund_err(self, data):
        self.slap_fund_error_slider.setAttributeValue(data)

    def read_slap_harm_err(self, data):
        self.slap_harm_error_slider.setAttributeValue(data)

    def read_slap_picomotor(self, data):
        self.slap_picomotor_edit.setAttributeValue(data)

    def write_slap_picomotor(self):
        new_power = self.slap_picomotor_edit.getWriteValue()
        logger.debug("In write_power: new value {0}".format(new_power))
        self.attributes["picomotor_pos_slap"].attr_write(new_power)

    def read_slap_fund_phase(self, data):
        self.slap_fund_phase_edit.setAttributeValue(data)

    def write_slap_fund_phase(self):
        new_value = self.slap_fund_phase_edit.getWriteValue()
        logger.debug("In write_slap_fund_phase: new value {0}".format(new_value))
        self.attributes["fund_phase_shift_slap"].attr_write(new_value)

    def read_slap_harm_phase(self, data):
        self.slap_harm_phase_edit.setAttributeValue(data)

    def write_slap_harm_phase(self):
        new_value = self.slap_harm_phase_edit.getWriteValue()
        logger.debug("In write_slap_harm_phase: new value {0}".format(new_value))
        self.attributes["harm_phase_shift_slap"].attr_write(new_value)

    def read_uv_energy(self, data):
        self.uv_energy_slider.setAttributeValue(data)

    def read_ir_energy(self, data):
        self.ir_energy_slider.setAttributeValue(data)

    def read_peakwavelength(self, data):
        self.vitara_l0_slider.setAttributeValue(data)

    def read_peakwidth(self, data):
        self.vitara_dl_slider.setAttributeValue(data)

    def read_spectrum(self, data):
        if self.wavelengths is not None:
            self.vitara_spectrum.setSpectrum(self.wavelengths, data)

    def read_wavelengths(self, data):
        self.wavelengths = data.value

    def cmd_done(self, data):
        print("Command done. Returned:\n{0}".format(data))

    def shutter_status(self, data):
        self.shutter_commands.setStatus(data, data.value)

    def shutter_open(self):
        self.devices["shutter"].command_inout_asynch("open_shutter", None, True)

    def shutter_close(self):
        self.devices["shutter"].command_inout_asynch("close_shutter", None, True)


if __name__ == "__main__":
    myappid = 'mycompany.myproduct.subproduct.version'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
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
    myapp.setWindowIcon(QtGui.QIcon("estrella_beer_2.png"))
    myapp.show()
    splash.finish(myapp)
    app.setWindowIcon(QtGui.QIcon("estrella_beer_2.png"))
    sys.exit(app.exec_())
