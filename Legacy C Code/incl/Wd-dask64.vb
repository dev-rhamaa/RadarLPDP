Option Strict Off
Option Explicit On

Imports System.Runtime.InteropServices
Imports System

Module WD_DASK
	
	'ADLink PCI Card Type
	Public Const PCI_9820 As Short = 1

  Public Const PXI_9816D As Short = &H2
  Public Const PXI_9826D As Short = &H3
  Public Const PXI_9846D As Short = &H4
	Public Const PXI_9846DW As Short = &H4
	Public Const PXI_9816H As Short = &H5
	Public Const PXI_9826H As Short = &H6
	Public Const PXI_9846H As Short = &H7
	Public Const PXI_9846HW As Short = &H7
	Public Const PXI_9816V As Short = &H8
	Public Const PXI_9826V As Short = &H9
	Public Const PXI_9846V As Short = &HA
	Public Const PXI_9846VW As Short = &HA
	'PCI 98x6 devices
	Public Const PCI_9816D As Short = &H12
	Public Const PCI_9826D As Short = &H13
	Public Const PCI_9846D As Short = &H14
	Public Const PCI_9846DW As Short = &H14
	Public Const PCI_9816H As Short = &H15
	Public Const PCI_9826H As Short = &H16
	Public Const PCI_9846H As Short = &H17
	Public Const PCI_9846HW As Short = &H17
	Public Const PCI_9816V As Short = &H18
	Public Const PCI_9826V As Short = &H19
	Public Const PCI_9846V As Short = &H1A
	Public Const PCI_9846VW As Short = &H1A	
	'PCIe 98x6 devices
	Public Const PCIe_9816D As Short = &H22
	Public Const PCIe_9826D As Short = &H23
	Public Const PCIe_9846D As Short = &H24
	Public Const PCIe_9846DW As Short = &H24
	Public Const PCIe_9816H As Short = &H25
	Public Const PCIe_9826H As Short = &H26
	Public Const PCIe_9846H As Short = &H27
	Public Const PCIe_9846HW As Short = &H27
	Public Const PCIe_9816V As Short = &H28
	Public Const PCIe_9826V As Short = &H29
	Public Const PCIe_9846V As Short = &H2A
	Public Const PCIe_9846VW As Short = &H2A
	'PCie 9842 device
	Public Const PCIe_9842 As Short = &H30
	'PXIe 9848 device
	Public Const PXIe_9848 As Short = &H32
	'PCIe 9852 device
	Public Const PCIe_9852 As Short = &H33
	'PXIe 9852 device
	Public Const PXIe_9852 As Short = &H34	
	
	'obsolete
	Public Const PCI_9816 As Short = 2
	Public Const PCI_9826 As Short = 3
	Public Const PCI_9846 As Short = 4	
	
	Public Const MAX_CARD As Short = 32
	
	'Error Code
	Public Const NoError As Short = 0
	Public Const ErrorUnknownCardType As Short = -1
	Public Const ErrorInvalidCardNumber As Short = -2
	Public Const ErrorTooManyCardRegistered As Short = -3
	Public Const ErrorCardNotRegistered As Short = -4
	Public Const ErrorFuncNotSupport As Short = -5
	Public Const ErrorInvalidIoChannel As Short = -6
	Public Const ErrorInvalidAdRange As Short = -7
	Public Const ErrorContIoNotAllowed As Short = -8
	Public Const ErrorDiffRangeNotSupport As Short = -9
	Public Const ErrorLastChannelNotZero As Short = -10
	Public Const ErrorChannelNotDescending As Short = -11
	Public Const ErrorChannelNotAscending As Short = -12
	Public Const ErrorOpenDriverFailed As Short = -13
	Public Const ErrorOpenEventFailed As Short = -14
	Public Const ErrorTransferCountTooLarge As Short = -15
	Public Const ErrorNotDoubleBufferMode As Short = -16
	Public Const ErrorInvalidSampleRate As Short = -17
	Public Const ErrorInvalidCounterMode As Short = -18
	Public Const ErrorInvalidCounter As Short = -19
	Public Const ErrorInvalidCounterState As Short = -20
	Public Const ErrorInvalidBinBcdParam As Short = -21
	Public Const ErrorBadCardType As Short = -22
	Public Const ErrorInvalidDaRange As Short = -23
	Public Const ErrorAdTimeOut As Short = -24
	Public Const ErrorNoAsyncAI As Short = -25
	Public Const ErrorNoAsyncAO As Short = -26
	Public Const ErrorNoAsyncDI As Short = -27
	Public Const ErrorNoAsyncDO As Short = -28
	Public Const ErrorNotInputPort As Short = -29
	Public Const ErrorNotOutputPort As Short = -30
	Public Const ErrorInvalidDioPort As Short = -31
	Public Const ErrorInvalidDioLine As Short = -32
	Public Const ErrorContIoActive As Short = -33
	Public Const ErrorDblBufModeNotAllowed As Short = -34
	Public Const ErrorConfigFailed As Short = -35
	Public Const ErrorInvalidPortDirection As Short = -36
	Public Const ErrorBeginThreadError As Short = -37
	Public Const ErrorInvalidPortWidth As Short = -38
	Public Const ErrorInvalidCtrSource As Short = -39
	Public Const ErrorOpenFile As Short = -40
	Public Const ErrorAllocateMemory As Short = -41
	Public Const ErrorDaVoltageOutOfRange As Short = -42
	Public Const ErrorInvalidSyncMode As Short = -43
	Public Const ErrorInvalidBufferID As Short = -44
	Public Const ErrorInvalidCNTInterval As Short = -45
	Public Const ErrorReTrigModeNotAllowed As Short = -46
	Public Const ErrorResetBufferNotAllowed As Short = -47
	Public Const ErrorAnaTriggerLevel As Short = -48
	Public Const ErrorDAQEvent As Short = -49
	Public Const ErrorInvalidDataSize As Short = -50
	Public Const ErrorOffsetCalibration As Short = -51
	Public Const ErrorGainCalibration As Short = -52
	Public Const ErrorCountOutofSDRAMSize As Short = -53
	Public Const ErrorNotStartTriggerModule As Short = -54
	Public Const ErrorInvalidRouteLine As Short = -55
	Public Const ErrorInvalidSignalCode As Short = -56
	Public Const ErrorInvalidSignalDirection As Short = -57
	Public Const ErrorTRGOSCalibration As Short = -58
  Public Const ErrorNoSDRAM As Short = -59
  Public Const ErrorIntegrationGain As Short = -60
  Public Const ErrorAcquisitionTiming As Short = -61
  Public Const ErrorIntegrationTiming As Short = -62
  Public Const ErrorInvalidTraceCnt As Short = -63
  Public Const ErrorTriggerSource As Short = -64
  Public Const ErrorInvalidTimeBase As Short = -70
  Public Const ErrorUndefinedParameter As Short = -71
  Public Const ErrorNotDAQSteppedMode As Short = -80
  Public Const ErrorBufAddrNotQuadDWordAlignment As Short = -90
	
	'Error number for calibration API 
  Public Const ErrorCalAddress As Short = -110
  Public Const ErrorInvalidCalBank As Short = -111
	
	'Error code for driver API
	Public Const ErrorConfigIoctl As Short = -201
	Public Const ErrorAsyncSetIoctl As Short = -202
	Public Const ErrorDBSetIoctl As Short = -203
	Public Const ErrorDBHalfReadyIoctl As Short = -204
	Public Const ErrorContOPIoctl As Short = -205
	Public Const ErrorContStatusIoctl As Short = -206
	Public Const ErrorPIOIoctl As Short = -207
	Public Const ErrorDIntSetIoctl As Short = -208
	Public Const ErrorWaitEvtIoctl As Short = -209
	Public Const ErrorOpenEvtIoctl As Short = -210
	Public Const ErrorCOSIntSetIoctl As Short = -211
	Public Const ErrorMemMapIoctl As Short = -212
	Public Const ErrorMemUMapSetIoctl As Short = -213
	Public Const ErrorCTRIoctl As Short = -214
	Public Const ErrorGetResIoctl As Short = -215
	
	'Synchronous Mode
	Public Const SYNCH_OP As Short = 1
	Public Const ASYNCH_OP As Short = 2
	
	'AD Range
	Public Const AD_B_10_V As Short = 1
	Public Const AD_B_5_V As Short = 2
	Public Const AD_B_2_5_V As Short = 3
	Public Const AD_B_1_25_V As Short = 4
	Public Const AD_B_0_625_V As Short = 5
	Public Const AD_B_0_3125_V As Short = 6
	Public Const AD_B_0_5_V As Short = 7
	Public Const AD_B_0_05_V As Short = 8
	Public Const AD_B_0_005_V As Short = 9
	Public Const AD_B_1_V As Short = 10
	Public Const AD_B_0_1_V As Short = 11
	Public Const AD_B_0_01_V As Short = 12
	Public Const AD_B_0_001_V As Short = 13
	Public Const AD_U_20_V As Short = 14
	Public Const AD_U_10_V As Short = 15
	Public Const AD_U_5_V As Short = 16
	Public Const AD_U_2_5_V As Short = 17
	Public Const AD_U_1_25_V As Short = 18
	Public Const AD_U_1_V As Short = 19
	Public Const AD_U_0_1_V As Short = 20
	Public Const AD_U_0_01_V As Short = 21
	Public Const AD_U_0_001_V As Short = 22
	Public Const AD_B_2_V As Short = 23
	Public Const AD_B_0_25_V As Short = 24
	Public Const AD_B_0_2_V As Short = 25
	Public Const AD_U_4_V As Short = 26
	Public Const AD_U_2_V As Short = 27
	Public Const AD_U_0_5_V As Short = 28
	Public Const AD_U_0_4_V As Short = 29
	Public Const AD_B_1_5_V As Short = 30
	Public Const AD_B_0_2145_V As Short = 31	
	
	'Constants for WD-DASK
	Public Const All_Channels As Short = -1
	
	Public Const WD_AI_ADCONVSRC_TimePacer As Short = &H0s
	
	Public Const WD_AI_TRGSRC_SOFT As Short = 0
	Public Const WD_AI_TRGSRC_ANA As Short = 1
	Public Const WD_AI_TRGSRC_ExtD As Short = 2
	Public Const WD_AI_TRSRC_SSI_1 As Short = 3
	Public Const WD_AI_TRSRC_SSI_2 As Short = 4
	Public Const WD_AI_TRSRC_PXIStar As Short = 5
	Public Const WD_AI_TRSRC_PXIeStar As Short = 6	
	'obsolete
	Public Const WD_AI_TRSRC_PXIStart As Short = 5
	
	Public Const WD_AI_TRGMOD_POST As Short = 0 'Post Trigger Mode
	Public Const WD_AI_TRGMOD_PRE As Short = 1 'Pre-Trigger Mode
	Public Const WD_AI_TRGMOD_MIDL As Short = 2 'Middle Trigger Mode
	Public Const WD_AI_TRGMOD_DELAY As Short = 3 'Delay Trigger Mode
	Public Const WD_AI_TrgPositive As Short = 1
	Public Const WD_AI_TrgNegative As Short = 0
	'---------- Constants for Analog trigger ------------
	Public Const CH0ATRIG As Short = 0
	Public Const CH1ATRIG As Short = 1
	Public Const CH2ATRIG As Short = 2
	Public Const CH3ATRIG As Short = 3	
	Public Const CH4ATRIG As Short = 4
	Public Const CH5ATRIG As Short = 5
	Public Const CH6ATRIG As Short = 6
	Public Const CH7ATRIG As Short = 7	
	'----------- Time Base -------------------
	Public Const WD_ExtTimeBase As Short = &H0s
	Public Const WD_SSITimeBase As Short = &H1s
	Public Const WD_StarTimeBase As Short = &H2s
	Public Const WD_IntTimeBase As Short = &H3s
	public const WD_PXI_CLK10 As Short = &H4s
	Public Const WD_PLL_REF_PXICLK10 As Short = &H4s
	Public Const WD_PLL_REF_EXT10 As Short = &H5s
	Public Const WD_PXIe_CLK100 As Short = &H6s
	Public Const WD_PLL_REF_PXIeCLK100 As Short = &H6s
	
	'SSI signal code
	Public Const SSI_TIME As Short = 15
	Public Const SSI_TRIG_SRC1 As Short = 7
	Public Const SSI_TRIG_SRC2 As Short = 5
	Public Const SSI_TRIG_SRC2_S As Short = 5
	Public Const SSI_TRIG_SRC2_T As Short = 6
	public const SSI_PRE_DATA_RDY As Short = &H10s
	'signal lines
	Public Const PXI_TRIG_0 As Short = 0
	Public Const PXI_TRIG_1 As Short = 1
	Public Const PXI_TRIG_2 As Short = 2
	Public Const PXI_TRIG_3 As Short = 3
	Public Const PXI_TRIG_4 As Short = 4
	Public Const PXI_TRIG_5 As Short = 5
	Public Const PXI_TRIG_6 As Short = 6
	Public Const PXI_TRIG_7 As Short = 7
	Public Const PXI_STAR_TRIG As Short = 8
	Public Const TRG_IO As Short = 9
		
	'obsolete
	Public Const PXI_START_TRIG As Short = 8
	
	'SSI cable lines
	public const SSI_LINE_0 As Short = 0
	public const SSI_LINE_1 As Short = 1
	public const SSI_LINE_2 As Short = 2
	public const SSI_LINE_3 As Short = 3
	public const SSI_LINE_4 As Short = 4
	public const SSI_LINE_5 As Short = 5
	public const SSI_LINE_6 As Short = 6
	public const SSI_LINE_7 As Short = 7
		
	'Software trigger op code
	Public Const SOFTTRIG_AI As Short = &H1s
	Public Const SOFTTRIG_AI_OUT As Short = &H2s
		
	'DAQ Event type for the event message
	Public Const DAQEnd As Short = 0
	Public Const DBEvent As Short = 1
	Public Const TrigEvent As Short = 2
	
	'DAQ advanced mode
	Public Const DAQSTEPPED As Short = 1
	Public Const RestartEn As Short = 2
	Public Const DualBufEn As Short = 4
	Public Const ManualSoftTrg As Short = &H40s
	public const AI_AVE As Short = 8	
	public const AI_AVE_32 As Short = &H10s
	
	'AI channel parameter item
	Public Const AI_RANGE As Short = 0
	Public Const AI_IMPEDANCE As Short = 1
	Public Const ADC_DITHER As Short = 2
	Public Const AI_COUPLING As Short = 3
	Public Const ADC_Bandwidth As Short = 4
	
	'AI channel parameter value
	Public Const IMPEDANCE_50Ohm As Short = 0
	Public Const IMPEDANCE_HI As Short = 1

	Public Const ADC_DITHER_DIS As Short = 0
	Public Const ADC_DITHER_EN As Short = 1

	Public Const DC_Coupling As Short = 0
	Public Const AC_Coupling As Short = 1

	Public Const BANDWIDTH_DEVICE_DEFAULT As Short = 0
	Public Const BANDWIDTH_20M  As Short = 20
	Public Const BANDWIDTH_100M As Short = 100
	
	'TrigOUT Channel Config	
	Public Const AITRIGOUT_CH0 As Short = 0
	Public Const AITRIGOUT_PXI As Short = 2
	Public Const AITRIGOUT_PXI_TRIG_0 As Short = 2
	Public Const AITRIGOUT_PXI_TRIG_1 As Short = 3
	Public Const AITRIGOUT_PXI_TRIG_2 As Short = 4
	Public Const AITRIGOUT_PXI_TRIG_3 As Short = 5
	Public Const AITRIGOUT_PXI_TRIG_4 As Short = 6
	Public Const AITRIGOUT_PXI_TRIG_5 As Short = 7
	Public Const AITRIGOUT_PXI_TRIG_6 As Short = 8
	Public Const AITRIGOUT_PXI_TRIG_7 As Short = 9
	
  'DIO Port Direction
  Public Const INPUT_PORT As Short = 1
  Public Const OUTPUT_PORT As Short = 2
	'DIO Line Direction
  Public Const INPUT_LINE As Short = 1
  Public Const OUTPUT_LINE As Short = 2
	'DIO mode
  Public Const SDI_En As Short = 0
  Public Const SDI_Dis As Short = 1
	
	'Calibration Action
  Public Const CalLoad As Short = 0
  Public Const AutoCal As Short = 1
  Public Const CalCopy As Short = 2
	
	'TrigOUT Width Config	
	Public Const WD_OutTrgPWidth_50ns As Short = 0
	Public Const WD_OutTrgPWidth_100ns As Short = 1
	Public Const WD_OutTrgPWidth_150ns As Short = 2
	Public Const WD_OutTrgPWidth_200ns As Short = 3
	Public Const WD_OutTrgPWidth_500ns As Short = 4
	Public Const WD_OutTrgPWidth_1us As Short = 5
	Public Const WD_OutTrgPWidth_2us As Short = 6
	Public Const WD_OutTrgPWidth_5us As Short = 7
	Public Const WD_OutTrgPWidth_10us As Short = 8
	'TrigOUT SRC/POL Config
	public const WD_OutTrgSrcAuto As Short = &H0s
	public const WD_OutTrgSrcManual As Short = &H1s
	public const WD_OutTrg_Rising As Short = &H0s
	public const WD_OutTrg_Fall As Short = &H10s	

  <StructLayout(LayoutKind.Sequential)> _
  Public Structure WD_DEVICE
        Public wModuleType As Short
        Public wCardID As Short
        Public geo_addr As Short
        Public Reserved As Short
        <MarshalAs(UnmanagedType.ByValTStr, SizeConst:=64)> Public dispname As String
  End Structure
    			
	Declare Function WaitForSingleObject Lib "kernel32" (ByVal hHandle As Integer, ByVal dwMilliseconds As Integer) As Integer
	Public Delegate Sub CallbackDelegate()

	'-------------------------------------------------------------------
	'  WD-DASK Function prototype
	'-----------------------------------------------------------------*/
	Declare Function WD_Register_Card Lib "WD-Dask64.dll" (ByVal CardType As Short, ByVal card_num As Short) As Short
	Declare Function WD_Register_Card_By_PXISlot_GA Lib "WD-Dask64.dll" (ByVal CardType As Short, ByVal geo_addr As Short) As Short
	Declare Function WD_Release_Card Lib "WD-Dask64.dll" (ByVal CardNumber As Short) As Short
	Declare Function WD_Get_SDRAMSize Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByRef sdramsize As Integer) As Short
	Declare Function WD_GetBaseAddr Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByRef BaseAddr As Integer, ByRef BaseAddr2 As Integer) As Short
	Declare Function WD_SoftTriggerGen Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal op As Byte) As Short
  Declare Function WD_GetActualRate Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal fdir As Byte, ByVal ActualRate As Double, ByRef interval As Integer, ByRef ActualRate As Double) As Short
	Declare Function WD_GetPXIGeographAddr Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByRef geo_addr As Byte) As Short
  Declare Function WD_Buffer_Alloc Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal dwSize As UInteger) As IntPtr
	Declare Function WD_Buffer_Free Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal buf As IntPtr) As Integer
	Declare Function WD_Device_Scan Lib "WD-Dask64.dll" (<[In](), Out()> ByVal AvailModules() As WD_DEVICE, ByVal ncount As Integer, ByRef retcnt As Integer) As Integer
	Declare Function WD_GetFPGAVersion Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByRef version As UInt32) As Short
	    
	'AI Functions
	Declare Function WD_AI_CH_Config Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal channel As Short, ByVal AdRange As Short) As Short
	Declare Function WD_AI_Config Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal TimeBase As Short, ByVal adDutyRestore As Byte, ByVal ConvSrc As Short, ByVal doubleEdged As Byte, ByVal AutoResetBuf As Byte) As Short
	Declare Function WD_AI_Set_Mode Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal modeCtrl As Short, ByVal wIter As Short) As Short
	Declare Function WD_AI_Trig_Config Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal trigMode As Short, ByVal TrigSrc As Short, ByVal trigPol As Short, ByVal anaTrigChan As Short, ByVal anaTriglevel As Double, ByVal postTrigScans As Integer, ByVal preTrigScans As Integer, ByVal trigDelayTicks As Integer, ByVal reTrgCnt As Integer) As Short
	Declare Function WD_OutTrig_Config Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal trig_Ch As Short, ByVal trig_conf As Short, ByVal trig_width As Short) As Short	
	Declare Function WD_AI_AsyncCheck Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByRef Stopped As Byte, ByRef AccessCnt As Integer) As Short
	Declare Function WD_AI_AsyncClear Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByRef startPos As Integer, ByRef AccessCnt As Integer) As Short
	Declare Function WD_AI_AsyncClearEx Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByRef startPos As Integer, ByRef AccessCnt As Integer, ByVal NoWait As Integer) As Short	
	Declare Function WD_AI_AsyncDblBufferHalfReady Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByRef HalfReady As Byte, ByRef StopFlag As Byte) As Short
	Declare Function WD_AI_AsyncDblBufferMode Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal enable As Byte) As Short
	Declare Function WD_AI_AsyncDblBufferToFile Lib "WD-Dask64.dll" (ByVal CardNumber As Short) As Short
	Declare Function WD_AI_ContReadChannel Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal channel As Short, ByVal BufId As Short, ByVal ReadScans As Integer, ByVal ScanIntrv As Integer, ByVal SampIntrv As Integer, ByVal SyncMode As Short) As Short
	Declare Function WD_AI_ContScanChannels Lib "WD-Dask64.dll" (ByVal wCardNumber As Short, ByVal wChannel As Short, ByVal BufId As Short, ByVal ReadScans As Integer, ByVal ScanIntrv As Integer, ByVal SampIntrv As Integer, ByVal SyncMode As Short) As Short
	Declare Function WD_AI_ContReadMultiChannels Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal NumChans As Short, ByRef chans As Short, ByVal BufId As Short, ByVal ReadScans As Integer, ByVal ScanIntrv As Integer, ByVal SampIntrv As Integer, ByVal SyncMode As Short) As Short
	Declare Function WD_AI_ContReadChannelToFile Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal channel As Short, ByVal BufId As Short, ByVal FileName As String, ByVal ReadScans As Integer, ByVal ScanIntrv As Integer, ByVal SampIntrv As Integer, ByVal SyncMode As Short) As Short
	Declare Function WD_AI_ContScanChannelsToFile Lib "WD-Dask64.dll" (ByVal wCardNumber As Short, ByVal wChannel As Short, ByVal BufId As Short, ByVal FileName As String, ByVal dwReadScans As Integer, ByVal ScanIntrv As Integer, ByVal SampIntrv As Integer, ByVal SyncMode As Short) As Short
	Declare Function WD_AI_ContReadMultiChannelsToFile Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal NumChans As Short, ByRef chans As Short, ByVal BufId As Short, ByVal FileName As String, ByVal ReadScans As Integer, ByVal ScanIntrv As Integer, ByVal SampIntrv As Integer, ByVal SyncMode As Short) As Short
	Declare Function WD_AI_ContStatus Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByRef status As Integer) As Short
	Declare Function WD_AI_InitialMemoryAllocated Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByRef MemSize As Integer) As Short
 	Declare Function WD_AI_VoltScale Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal AdRange As Short, ByVal reading As Short, ByRef Voltage As Double) As Short
  Declare Function WD_AI_VoltScale32 Lib "WD-Dask.dll" (ByVal CardNumber As Short, ByVal AdRange As Short, ByVal reading As Integer, ByRef Voltage As Double) As Short 	
 	Declare Function WD_AI_ContVScale Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal AdRange As Short, ByVal readingArray() As Short, ByVal voltageArray() As Double, ByVal count As Integer) As Short
 	Declare Function WD_AI_ContVScale Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal AdRange As Short, ByVal readingArray As IntPtr, ByVal voltageArray() As Double, ByVal count As Integer) As Short
 	Declare Function WD_AI_ContVScale Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal AdRange As Short, ByVal readingArray As IntPtr, ByVal voltageArray As IntPtr, ByVal count As Integer) As Short
 	Declare Function WD_AI_ContVScaleEx Lib "WD-Dask.dll" (ByVal CardNumber As Short, ByVal AdRange As Short, ByVal width As Short, ByRef readingArray As Integer, ByRef voltageArray As Double, ByVal count As Integer) As Short

 	Declare Function WD_AI_ContBufferSetup Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal Buffer() As Short, ByVal ReadCount As Integer, ByRef BufferId As UShort) As Short
	Declare Function WD_AI_ContBufferSetup Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal Buffer As IntPtr, ByVal ReadCount As Integer, ByRef BufferId As UShort) As Short
  Declare Function WD_AI_ContBufferSetup32 Lib "WD-Dask.dll" (ByVal CardNumber As Short, ByRef Buffer As Integer, ByVal ReadCount As Integer, ByRef BufferId As UShort) As Short

	Declare Function WD_AI_ContBufferReset Lib "WD-Dask64.dll" (ByVal CardNumber As Short) As Short
	Declare Function WD_AI_DMA_Transfer Lib "WD-Dask64.dll" (ByVal CardNumber As Short) As Short
	Declare Function WD_AI_ConvertCheck Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByRef StopFlag As Byte) As Short
	Declare Function WD_AI_AsyncReStartNextReady Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByRef DaqReady As Byte, ByRef StopFlag As Byte, ByRef RdyDaqCnt As Byte) As Short
    	Declare Function WD_AI_EventCallBack_x64 Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal Mode As Short, ByVal EventType As Short, ByVal callbackAddr As CallbackDelegate) As Short
    	
	Declare Function WD_AI_SetTimeout Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal msec As UInteger) As Short
	Declare Function WD_AI_AsyncDblBufferOverrun Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal op As Short, ByRef overrunFlag As Short) As Short
	Declare Function WD_AI_AsyncDblBufferHandled Lib "WD-Dask64.dll" (ByVal CardNumber As Short) As Short
	Declare Function WD_AI_AsyncReTrigNextReady Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByRef trgReady As Byte, ByRef StopFlag As Byte, ByRef RdyTrigCnt As Integer) As Short     
	
	'SSI Functions
	Declare Function WD_SSI_SourceConn Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal sigCode As Short) As Short
	Declare Function WD_SSI_SourceDisConn Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal sigCode As Short) As Short
	Declare Function WD_SSI_SourceClear Lib "WD-Dask64.dll" (ByVal CardNumber As Short) As Short
        Declare Function WD_Route_Signal Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal signal As Short, ByVal Line As Short, ByVal direct As Short) As Short
	Declare Function WD_Signal_DisConn Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal signal As Short, ByVal Line As Short) As Short
	
	'Calibration Functions
	Declare Function WD_AD_Auto_Calibration_ALL Lib "WD-Dask64.dll" (ByVal wCardNumber As Short) As Short
	Declare Function WD_EEPROM_CAL_Constant_Update Lib "WD-Dask64.dll" (ByVal wCardNumber As Short, ByVal bank As Short) As Short
	Declare Function WD_Load_CAL_Data Lib "WD-Dask64.dll" (ByVal wCardNumber As Short, ByVal bank As Short) As Short
	Declare Function WD_Set_Default_Load_Area Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal bank As Short) As Short
	Declare Function WD_Get_Default_Load_Area Lib "WD-Dask64.dll" (ByVal CardNumber As Short) As Short	

	'DI Functions
	Declare Function WD_DI_ReadPort Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal Port As Short, ByRef Value As Integer) As Short
	Declare Function WD_DI_ReadLine Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal Port As Short, ByVal Line As Short, ByRef Value As Short) As Short
	
	'DO Functions
	Declare Function WD_DO_WritePort Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal Port As Short, ByVal Value As Integer) As Short
	Declare Function WD_DO_WriteLine Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal Port As Short, ByVal Line As Short, ByVal Value As Short) As Short
	Declare Function WD_DO_ReadLine Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal Port As Short, ByVal Line As Short, ByRef Value As Short) As Short
	Declare Function WD_DO_ReadPort Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal Port As Short, ByRef Value As Integer) As Short
	
	'DIO Functions
	Declare Function WD_DIO_PortConfig Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal Port As Short, ByVal mode As Short, ByVal Direction As Short) As Short
	Declare Function WD_DIO_LineConfig Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal Port As Short, ByVal wLine As Integer , ByVal Direction As Short) As Short
	Declare Function WD_DIO_LinesConfig Lib "WD-Dask64.dll" (ByVal CardNumber As Short, ByVal Port As Short, ByVal mode As Short, ByVal wLinesdirmap As Integer) As Short

End Module