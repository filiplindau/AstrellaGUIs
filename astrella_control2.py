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
sys.path.append('../TangoWidgetsQt5')
import striptool
from TangoDeviceClient import TangoDeviceClient
from ColorDefinitions import QTangoSizes
from SliderCompositeWidgets import QTangoAttributeSlider
from SpectrumCompositeWidgets import QTangoReadAttributeSpectrum
from ButtonWidgets import QTangoCommandSelection
from LabelWidgets import QTangoStartLabel, QTangoAttributeUnitLabel, QTangoReadAttributeLabel
from LabelCompositeWidgets import QTangoDeviceNameStatus, QTangoReadAttributeBoolean
from EditWidgets import QTangoReadAttributeSpinBox, QTangoWriteAttributeSpinBox

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

        self.verdi_power_slider = QTangoAttributeSlider(self.attr_sizes, self.colors, show_write_widget=True, slider_style=4)
        self.verdi_power_slider.setSliderLimits(0, 6.5)
        self.verdi_power_slider.setAttributeName("Verdi Power")
        self.verdi_power_slider.newWriteValueSignal.connect(self.write_verdi_power)

        self.add_attribute("power", "verdi", self.read_verdi_power, update_interval=0.3, single_shot=False,
                           get_info=True, attr_info_slot=self.verdi_power_slider.configureAttribute)

        self.verdi_temperature_slider = QTangoAttributeSlider(self.attr_sizes, self.colors, show_write_widget=False,
                                                              slider_style=4)
        self.verdi_temperature_slider.setSliderLimits(10, 25)
        self.verdi_temperature_slider.setAttributeName("Verdi Temp")
        self.add_attribute("temperature_main", "verdi", self.read_verdi_temperature, update_interval=0.5, single_shot=False,
                           get_info=True, attr_info_slot=self.verdi_temperature_slider.configureAttribute)

        self.verdi_current_slider = QTangoAttributeSlider(self.attr_sizes, self.colors, show_write_widget=False,
                                                              slider_style=4)
        self.verdi_current_slider.setSliderLimits(0, 40)
        self.verdi_current_slider.setAttributeName("Verdi Current")
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

        self.revolution_power_slider = QTangoAttributeSlider(self.attr_sizes, self.colors, show_write_widget=False, slider_style=4)
        self.revolution_power_slider.setSliderLimits(0, 30)
        self.revolution_power_slider.setAttributeName("Rev Power")
        self.add_attribute("pd_power", "revolution", self.read_revolution_power, update_interval=0.3, single_shot=False,
                           get_info=True, attr_info_slot=self.revolution_power_slider.configureAttribute)

        self.revolution_temp_slider = QTangoAttributeSlider(self.attr_sizes, self.colors, show_write_widget=False,
                                                            slider_style=4)
        self.revolution_temp_slider.setSliderLimits(160, 250)
        self.revolution_temp_slider.setAttributeName("Rev Temp")
        self.add_attribute("head_temp", "revolution", self.read_revolution_temp, update_interval=0.5, single_shot=False,
                           get_info=True, attr_info_slot=self.revolution_temp_slider.configureAttribute)

        self.revolution_current_slider = QTangoAttributeSlider(self.attr_sizes, self.colors, show_write_widget=False,
                                                               slider_style=4)
        self.revolution_current_slider.setSliderLimits(0, 20)
        self.revolution_current_slider.setAttributeName("Rev Current")
        self.revolution_current_slider.newWriteValueSignal.connect(self.write_revolution_current)
        self.add_attribute("diode_current_actual", "revolution", self.read_revolution_current, update_interval=0.5, single_shot=False,
                           get_info=True, attr_info_slot=self.revolution_current_slider.configureAttribute)

        self.revolution_commands = QTangoCommandSelection("Revolution", self.attr_sizes, self.colors)
        self.revolution_commands.addCmdButton("On", self.revolution_on)
        self.revolution_commands.addCmdButton("Off", self.revolution_off)
        self.revolution_commands.addCmdButton("Operating", self.revolution_operating)
        self.add_attribute("state", "revolution", self.revolution_status, update_interval=0.3, single_shot=False)

        # Vitara setup
        #
        self.add_device("vitara", "astrella/oscillator/vitara")

        self.vitara_power_slider = QTangoAttributeSlider(self.attr_sizes, self.colors, show_write_widget=False, slider_style=4)
        self.vitara_power_slider.setSliderLimits(0, 700)
        self.vitara_power_slider.setAttributeName("Vitara Power")
        self.add_attribute("pd_power", "vitara", self.read_vitara_power, update_interval=0.3, single_shot=False,
                           get_info=True, attr_info_slot=self.vitara_power_slider.configureAttribute)
        self.add_attribute("modelock_status", "vitara", self.read_vitara_modelock, update_interval=0.5, single_shot=False,
                           get_info=False)
        self.vitara_modelock_label = QTangoReadAttributeBoolean(self.attr_sizes, self.colors)
        self.vitara_modelock_label.setAttributeName("Modelock")
        self.vitara_rasterizing_label = QTangoReadAttributeBoolean(self.attr_sizes, self.colors)
        self.vitara_rasterizing_label.setAttributeName("Rasterizing")
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
        self.vitara_l0_slider = QTangoAttributeSlider(self.attr_sizes, self.colors, show_write_widget=False, slider_style=4)
        self.vitara_l0_slider.setSliderLimits(700, 820)
        self.vitara_l0_slider.setAttributeName(u"Central \u03bb")

        self.vitara_dl_slider = QTangoAttributeSlider(self.attr_sizes, self.colors, show_write_widget=False, slider_style=4)
        self.vitara_dl_slider.setSliderLimits(0, 80)
        self.vitara_dl_slider.setAttributeName("Bandwidth")

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
        self.slap_commands.addCmdButton("Fund enable", self.slap_fund)
        self.slap_commands.addCmdButton("Harm enable", self.slap_harm)
        self.add_attribute("state", "slap", self.slap_status, update_interval=0.3, single_shot=False)
        # Separate slap gui? There is quite a lot to adjust.

        # Astrella setup
        #
        # Add energy device
        # Add Spectrometer device

        # THG setup
        #
        # Add energy device (same as astrella?)
        # Add spectrometer device

        # Set up layout
        #
        self.grid_layout = QtWidgets.QGridLayout()
        self.left_layout_top = QtWidgets.QVBoxLayout()
        self.right_layout_top = QtWidgets.QHBoxLayout()
        self.left_layout_bottom = QtWidgets.QVBoxLayout()
        self.right_layout_bottom = QtWidgets.QHBoxLayout()
        self.left_layout_top.setSpacing(16)
        self.left_layout_bottom.setSpacing(16)

        self.add_layout(self.grid_layout)
        self.grid_layout.addLayout(self.left_layout_top, 0, 0)
        self.grid_layout.addLayout(self.right_layout_top, 0, 1)
        s_widget = QtWidgets.QWidget()
        s_widget.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.grid_layout.addWidget(s_widget, 1, 0)
        self.grid_layout.addLayout(self.left_layout_bottom, 2, 0)
        self.grid_layout.addLayout(self.right_layout_bottom, 2, 1)

        # h_spacer_4 = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        # self.add_spaceritem(h_spacer_4)
        # self.add_layout(self.right_layout)

        self.left_layout_top.addWidget(self.verdi_commands)
        self.left_layout_top.addWidget(self.revolution_commands)
        self.left_layout_top.addWidget(self.sdg_commands)
        v_spacer_1 = QtWidgets.QSpacerItem(10, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.left_layout_top.addSpacerItem(v_spacer_1)
        # lay_verdi_sliders = QtWidgets.QHBoxLayout()
        self.right_layout_top.addWidget(self.verdi_power_slider)
        self.right_layout_top.addWidget(self.verdi_current_slider)
        self.right_layout_top.addWidget(self.verdi_temperature_slider)
        h_spacer_1 = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.right_layout_top.addSpacerItem(h_spacer_1)
        # self.left_layout.addLayout(lay_verdi_sliders)
        # lay_rev_sliders = QtWidgets.QHBoxLayout()
        self.right_layout_top.addWidget(self.revolution_power_slider)
        self.right_layout_top.addWidget(self.revolution_current_slider)
        self.right_layout_top.addWidget(self.revolution_temp_slider)
        h_spacer_2 = QtWidgets.QSpacerItem(10, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        # lay_rev_sliders.addSpacerItem(h_spacer_2)
        # self.left_layout.addLayout(lay_rev_sliders)

        self.left_layout_bottom.addWidget(self.vitara_commands)
        self.left_layout_bottom.addWidget(self.vitara_rasterizing_label)
        self.left_layout_bottom.addWidget(self.vitara_modelock_label)
        self.left_layout_bottom.addWidget(self.slap_commands)
        v_spacer_2 = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.left_layout_bottom.addSpacerItem(v_spacer_2)
        # lay_vitara_sliders = QtWidgets.QHBoxLayout()
        self.right_layout_bottom.addWidget(self.vitara_power_slider)
        self.right_layout_bottom.addWidget(self.vitara_l0_slider)
        self.right_layout_bottom.addWidget(self.vitara_dl_slider)
        h_spacer_2 = QtWidgets.QSpacerItem(10, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.right_layout_bottom.addSpacerItem(h_spacer_2)
        # self.right_layout.addLayout(lay_vitara_sliders)

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
        self.devices["slap"].write_attribute("fund_enabled", True)

    def slap_harm(self):
        self.devices["slap"].write_attribute("harm_enabled", True)

    def slap_status(self, data):
        self.slap_commands.setStatus(data, data.value)

    def cmd_done(self, data):
        print("Command done. Returned:\n{0}".format(data))


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
