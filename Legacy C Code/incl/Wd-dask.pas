unit WD-DASK;

interface

Const

(*-------- WD-DASK Card Type -----------*)
  PCI_9820  =  1;

  PXI_9816D =  $2;
  PXI_9826D =  $3;
  PXI_9846D =  $4;
  PXI_9846DW = $4;
  PXI_9816H =  $5;
  PXI_9826H =  $6;
  PXI_9846H =  $7;
  PXI_9846HW = $7;
  PXI_9816V =  $8;
  PXI_9826V =  $9;
  PXI_9846V =  $a;
  PXI_9846VW = $a;
  
 (*-PCI 98x6 devices-*)
  PCI_9816D =  $12;
  PCI_9826D =  $13;
  PCI_9846D =  $14;
  PCI_9846DW = $14;
  PCI_9816H =  $15;
  PCI_9826H =  $16;
  PCI_9846H =  $17;
  PCI_9846HW = $17;
  PCI_9816V =  $18;
  PCI_9826V =  $19;
  PCI_9846V =  $1a;
  PCI_9846VW = $1a;
  
 (*-PCIe 98x6 devices-*)
  PCIe_9816D =  $22;
  PCIe_9826D =  $23;
  PCIe_9846D =  $24;
  PCIe_9846DW = $24;
  PCIe_9816H =  $25;
  PCIe_9826H =  $26;
  PCIe_9846H =  $27;
  PCIe_9846HW = $27;
  PCIe_9816V =  $28;
  PCIe_9826V =  $29;
  PCIe_9846V =  $2a;
  PCIe_9846VW = $2a;
  
  PCIe_9842   = $30;
  PXIe_9848   = $32;
  PCIe_9852   = $33;
  PXIe_9852   = $34;
    
 (*----obsolete----*)
  PCI_9816  =  2;
  PCI_9826  =  3;
  PCI_9846  =  4;
  
  MAX_CARD   = 32;

(*-------- Error Number -----------*)
  NoError                    =  0;
  ErrorUnknownCardType       = -1;
  ErrorInvalidCardNumber     = -2;
  ErrorTooManyCardRegistered = -3;
  ErrorCardNotRegistered     = -4;
  ErrorFuncNotSupport        = -5;
  ErrorInvalidIoChannel      = -6;
  ErrorInvalidAdRange        = -7;
  ErrorContIoNotAllowed      = -8;
  ErrorDiffRangeNotSupport   = -9;
  ErrorLastChannelNotZero    = -10;
  ErrorChannelNotDescending  = -11;
  ErrorChannelNotAscending   = -12;
  ErrorOpenDriverFailed      = -13;
  ErrorOpenEventFailed       = -14;
  ErrorTransferCountTooLarge = -15;
  ErrorNotDoubleBufferMode   = -16;
  ErrorInvalidSampleRate     = -17;
  ErrorInvalidCounterMode    = -18;
  ErrorInvalidCounter        = -19;
  ErrorInvalidCounterState   = -20;
  ErrorInvalidBinBcdParam    = -21;
  ErrorBadCardType           = -22;
  ErrorInvalidDaRefVoltage   = -23;
  ErrorAdTimeOut             = -24;
  ErrorNoAsyncAI             = -25;
  ErrorNoAsyncAO             = -26;
  ErrorNoAsyncDI             = -27;
  ErrorNoAsyncDO             = -28;
  ErrorNotInputPort          = -29;
  ErrorNotOutputPort         = -30;
  ErrorInvalidDioPort        = -31;
  ErrorInvalidDioLine        = -32;
  ErrorContIoActive          = -33;
  ErrorDblBufModeNotAllowed  = -34;
  ErrorConfigFailed          = -35;
  ErrorInvalidPortDirection  = -36;
  ErrorBeginThreadError      = -37;
  ErrorInvalidPortWidth      = -38;
  ErrorInvalidCtrSource      = -39;
  ErrorOpenFile              = -40;
  ErrorAllocateMemory        = -41;
  ErrorDaVoltageOutOfRange   = -42;
  ErrorInvalidSyncMode       = -43;
  ErrorInvalidBufferID       = -44;
  ErrorInvalidCNTInterval    = -45;
  ErrorReTrigModeNotAllowed  = -46;
  ErrorResetBufferNotAllowed = -47;
  ErrorAnaTriggerLevel       = -48;
  ErrorDAQEvent		     = -49;
  ErrorInvalidDataSize       = -50;
  ErrorOffsetCalibration     = -51;
  ErrorGainCalibration	     = -52;
  ErrorCountOutofSDRAMSize   = -53;
  ErrorNotStartTriggerModule = -54;
  ErrorInvalidRouteLine      = -55;
  ErrorInvalidSignalCode     = -56;
  ErrorInvalidSignalDirection = -57;
  ErrorTRGOSCalibration	  = -58;
  
  ErrorNoSDRAM   	     = -59;
  ErrorIntegrationGain       = -60;
  ErrorAcquisitionTiming     = -61;
  ErrorIntegrationTiming     = -62;
  ErrorInvalidTraceCnt   = -63;
  ErrorTriggerSource      = -64;
  ErrorInvalidTimeBase      = -71;
  ErrorUndefinedParameter   = -56;
  ErrorNotDAQSteppedMode = -80;
  ErrorBufAddrNotQuadDWordAlignment = -90;

(*--Error number for calibration API--*)
  ErrorCalAddress = -110;
  ErrorInvalidCalBank = -111;
 
  ErrorConfigIoctl           = -201;
  ErrorAsyncSetIoctl         = -202;
  ErrorDBSetIoctl            = -203;
  ErrorDBHalfReadyIoctl      = -204;
  ErrorContOPIoctl           = -205;
  ErrorContStatusIoctl       = -206;
  ErrorPIOIoctl              = -207;
  ErrorDIntSetIoctl          = -208;
  ErrorWaitEvtIoctl          = -209;
  ErrorOpenEvtIoctl          = -210;
  ErrorCOSIntSetIoctl        = -211;
  ErrorMemMapIoctl           = -212;
  ErrorMemUMapSetIoctl       = -213;
  ErrorCTRIoctl              = -214;

(*-------- Synchronous Mode -----------*)
  SYNCH_OP  = 1;
  ASYNCH_OP = 2;

(*-------- AD Range -----------*)
  AD_B_10_V     =  1;
  AD_B_5_V      =  2;
  AD_B_2_5_V    =  3;
  AD_B_1_25_V   =  4;
  AD_B_0_625_V  =  5;
  AD_B_0_3125_V =  6;
  AD_B_0_5_V    =  7;
  AD_B_0_05_V   =  8;
  AD_B_0_005_V  =  9;
  AD_B_1_V      = 10;
  AD_B_0_1_V    = 11;
  AD_B_0_01_V   = 12;
  AD_B_0_001_V  = 13;
  AD_U_20_V     = 14;
  AD_U_10_V     = 15;
  AD_U_5_V      = 16;
  AD_U_2_5_V    = 17;
  AD_U_1_25_V   = 18;
  AD_U_1_V      = 19;
  AD_U_0_1_V    = 20;
  AD_U_0_01_V   = 21;
  AD_U_0_001_V  = 22;
  AD_B_2_V	= 23;
  AD_B_0_25_V	= 24;
  AD_B_0_2_V	= 25;
  AD_U_4_V	= 26;
  AD_U_2_V	= 27;
  AD_U_0_5_V	= 28;
  AD_U_0_4_V	= 29;
  AD_B_1_5_V	= 30;
  AD_B_0_2145_V = 31;

(*-------- Constants for WD-DASK ------------*)
  All_Channels = -1;

 (*-- Constants for AI --*)
  WD_AI_ADCONVSRC_TimePacer = $0;

  WD_AI_TRGSRC_SOFT = $0;
  WD_AI_TRGSRC_ANA =  $1;
  WD_AI_TRGSRC_ExtD = $2;
  WD_AI_TRSRC_SSI_1 = $3;
  WD_AI_TRSRC_SSI_2 = $4;
  WD_AI_TRSRC_PXIStar = $5;
  WD_AI_TRSRC_PXIeStar = $6;  
  WD_AI_TRGMOD_POST = $0;    (*-- Post Trigger Mode --*)
  WD_AI_TRGMOD_PRE = $1;    (*-- Pre-Trigger Mode --*)
  WD_AI_TRGMOD_MIDL = $2;   (*-- Middle Trigger Mode --*)
  WD_AI_TRGMOD_DELAY = $3;   (*-- Delay Trigger Mode --*)
  WD_AI_TrgPositive = $1;
  WD_AI_TrgNegative = $0;
 
 (*-- obsolete)
  WD_AI_TRSRC_PXIStart = $5;
   
  WD_AIEvent_Manual = $80;  (* AI event manual reset     *)
 (*-- Analog trigger Dedicated Channel --*)
  CH0ATRIG = $0;
  CH1ATRIG = $1;
  CH2ATRIG = $2;
  CH3ATRIG = $3; 
  CH4ATRIG = $4;
  CH5ATRIG = $5;
  CH6ATRIG = $6;
  CH7ATRIG = $7;   
 (*-- Time Base --*)
  WD_ExtTimeBase = $0;
  WD_SSITimeBase = $1;
  WD_StarTimeBase = $2;
  WD_IntTimeBase = $3;
  WD_PXI_CLK10 = $4;
  WD_PLL_REF_PXICLK10 = $4;
  WD_PLL_REF_EXT10 = $5;
  WD_PXIe_CLK100 = $6;
  WD_PLL_REF_PXIeCLK100 = $6;

 (*-- SSI signal code --*)
  SSI_TIME	= 15;
  SSI_TRIG_SRC1	= 7;
  SSI_TRIG_SRC2	= 5;
  SSI_TRIG_SRC2_S = 5;
  SSI_TRIG_SRC2_T = 6;
 (*-- signal lines --*)
  PXI_TRIG_0 = $0;
  PXI_TRIG_1 = $1;
  PXI_TRIG_2 = $2;
  PXI_TRIG_3 = $3;
  PXI_TRIG_4 = $4;
  PXI_TRIG_5 = $5;
  PXI_TRIG_6 = $6;
  PXI_TRIG_7 = $7;
  PXI_STAR_TRIG = $8;  
  TRG_IO = $9;
  SSI_PRE_DATA_RDY = $10;
  
 (*-- obsolete)
  PXI_START_TRIG = $8;

 (*-- Software trigger op code --*)
  SOFTTRIG_AI	= 1;
  SOFTTRIG_AI_OUT  = 2;
  
 (*-- DAQ Event type for the event message --*)
  DAQEnd	= 0;
  DBEvent	= 1;
  TrigEvent	= 2;
  
 (*-- DAQ advanced mode --*)
  DAQSTEPPED = 1;
  RestartEn = 2;
  DualBufEn = 4;
  ManualSoftTrg = $40;
  DMASTEPPED = $80;
  AI_AVE = 8;
  AI_AVE_32 = $10;  

 (*-- ai channel parameter --*)
  AI_RANGE = 0;
  AI_IMPEDANCE = 1;
  ADC_DITHER =	2;
  AI_COUPLING = 3;
  ADC_Bandwidth = 4;

 (*-- ai channel parameter value --*)
  IMPEDANCE_50Ohm = 0;
  IMPEDANCE_HI = 1;

  ADC_DITHER_DIS = 0;
  ADC_DITHER_EN = 1;  

  DC_Coupling = 0;
  AC_Coupling = 1;
    
  BANDWIDTH_DEVICE_DEFAULT = 0;
  BANDWIDTH_20M = 20;  
  BANDWIDTH_100M = 100;  

 (*--------- Constants for TrigOUT Width ----------*)
  AITRIGOUT_CH0 = 0;
  AITRIGOUT_PXI = 2;
  AITRIGOUT_PXI_TRIG_0 = 2;
  AITRIGOUT_PXI_TRIG_1 = 3;
  AITRIGOUT_PXI_TRIG_2 = 4;
  AITRIGOUT_PXI_TRIG_3 = 5;
  AITRIGOUT_PXI_TRIG_4 = 6;
  AITRIGOUT_PXI_TRIG_5 = 7;
  AITRIGOUT_PXI_TRIG_6 = 8;  
  AITRIGOUT_PXI_TRIG_7 = 9;     
  
(*--------- Constants for DIO Port Direction ----------*)
 (*--- DIO Port Direction ---*)
  INPUT_PORT  = 1;
  OUTPUT_PORT = 2;
 (*--- DIO Line Direction ---*)
  INPUT_LINE  = 1;
  OUTPUT_LINE = 2;
 (*--- DIO mode ---*)
  SDI_En  = 0;
  SDI_Dis = 1;  
  
 (*--------- Constants for Calibration Action ----------*)
  CalLoad = 0;
  AutoCal = 1;
  CalCopy = 2;
  
 (*--------- Constants for TrigOUT Width ----------*)
  WD_OutTrgPWidth_50ns = $0;
  WD_OutTrgPWidth_100ns = $1;
  WD_OutTrgPWidth_150ns = $2;
  WD_OutTrgPWidth_200ns = $3;
  WD_OutTrgPWidth_500ns = $4;
  WD_OutTrgPWidth_1us = $5;
  WD_OutTrgPWidth_2us = $6;
  WD_OutTrgPWidth_5us = $7;
  WD_OutTrgPWidth_10us = $8;  

(*--------- TrigOUT SRC/POL Config ----------*)
  WD_OutTrgSrcAuto = $0;
  WD_OutTrgSrcManual = $1;
  WD_OutTrg_Rising  = $0;
  WD_OutTrg_Fall  = $10;
    
type
  TCallbackFunc = function : Integer;

type 
	WD_DEVICE = record
		wModuleType : Word;
		wCardID : Word;
		geo_addr : Word;
		Reserved : Word;	
  	dispname : Array [0..63] of char;
	end;

(****************************************************************************)
(*          WD-DASK Functions Declarations                                *)
(****************************************************************************)
function WD_Register_Card (CardType:Word; card_num:Word):Smallint;stdcall;
function WD_Register_Card_By_PXISlot_GA (CardType:Word; geo_addr:Word):Smallint;stdcall;
function WD_Release_Card  (CardNumber:Word):Smallint;stdcall;
function WD_Get_SDRAMSize  (CardNumber:Word; var MemSize:Cardinal):Smallint;stdcall;
function WD_SoftTriggerGen (CardNumber:Word; Stopped:Byte):Smallint;stdcall;
function WD_GetActualRate  (CardNumber:word; fdir:Byte; SampleRate:Double; var interval:Cardinal; var ActualRate:Double):Smallint;stdcall;
function WD_GetBaseAddr    (CardNumber:Word; var BaseAddr:Cardinal; var BaseAddr2:Cardinal):Smallint;stdcall;
function WD_GetPXIGeographAddr  (CardNumber:word; var geo_addr:Byte):Smallint;stdcall;
function WD_Buffer_Alloc  (CardNumber:Word; dwSize:Cardinal):Pointer;stdcall;
function WD_Buffer_Free  (CardNumber:word; BufferAddr:Pointer):BOOL;stdcall;
function WD_Device_Scan  (var AvailModules:WD_DEVICE; ncount:Word; var retcnt:Wprd):Smallint;stdcall;
function WD_GetFPGAVersion (CardNumber:Word; var version:Cardinal):Smallint;stdcall;
(*---------------------------------------------------------------------------*)
function WD_AI_Config (CardNumber:Word; TimeBase:Word; adDutyRestore:Byte; ConvSrc:Word; doubleEdged:Byte; AutoResetBuf:Byte):Smallint;stdcall;
function WD_AI_Trig_Config (CardNumber:Word; trigMode:Word; trigSrc:Word; trigPol:Word; anaTrigchan:Word; anaTriglevel:Double; postTrigScans:Cardinal; preTrigScans:Cardinal; trigDelayTicks:Cardinal; ReTrgCnt:Cardinal):Smallint;stdcall;
function WD_OutTrig_Config (CardNumber:Word; trig_Ch:Word; trig_conf:Word; trig_width:Word):Smallint;stdcall;
function WD_AI_CH_Config (CardNumber:Word; Channel:Word; AdRange:Word):Smallint;stdcall;
function WD_AI_CH_ChangeParam (CardNumber:Word; Channel:Word; wParam:Word; wValue:Word):Smallint;stdcall;
function WD_AI_Set_Mode (CardNumber:Word; modeCtrl:Word; wIter:Word):Smallint;stdcall;
function WD_AI_InitialMemoryAllocated (CardNumber:Word; var MemSize:Cardinal):Smallint;stdcall;
function WD_AI_VoltScale (CardNumber:Word; AdRange:Word; reading:Smallint; var voltage:Double):Smallint;stdcall;
function WD_AI_VoltScale32 (CardNumber:Word; AdRange:Word; reading:Longint; var voltage:Double):Smallint;stdcall;
function WD_AI_ContReadChannel (CardNumber:Word; Channel:Word; BufId:Word; ReadScans:Cardinal; ScanIntrv:Cardinal; SampIntrv:Cardinal; SyncMode:Word):Smallint;stdcall;
function WD_AI_ContReadMultiChannels (CardNumber:Word; NumChans:Word; var Chans:Word; BufId:Word; ReadScans:Cardinal;
               ScanIntrv:Cardinal; SampIntrv:Cardinal; SyncMode:Word):Smallint;stdcall;
function WD_AI_ContScanChannels (CardNumber:Word; Channel:Word; BufId:Word; ReadScans:Cardinal; ScanIntrv:Cardinal; SampIntrv:Cardinal; SyncMode:Word):Smallint;stdcall;
function WD_AI_ContReadChannelToFile (CardNumber:Word; Channel:Word; BufId:Word; var FileName:Char; ReadScans:Cardinal;
			   ScanIntrv:Cardinal; SampIntrv:Cardinal; SyncMode:Word):Smallint;stdcall;
function WD_AI_ContReadMultiChannelsToFile (CardNumber:Word; NumChans:Word; var Chans:Word;
               BufId:Word; var FileName:Byte; ReadScans:Cardinal;
               ScanIntrv:Cardinal; SampIntrv:Cardinal; SyncMode:Word):Smallint;stdcall;
function WD_AI_ContScanChannelsToFile (CardNumber:Word; Channel:Word; BufId:Word;
               var FileName:Char; ReadScans:Cardinal; ScanIntrv:Cardinal; SampIntrv:Cardinal; SyncMode:Word):Smallint;stdcall;
function WD_AI_ContVScale (CardNumber:Word; AdRange:Word; var readingArray:Word; var voltageArray:Double; count:Longint):Smallint;stdcall;
function WD_AI_ContStatus (CardNumber:Word; var Status:Cardinal):Smallint;stdcall;
function WD_AI_AsyncCheck (CardNumber:Word; var Stopped:Byte; var AccessCnt:Cardinal):Smallint;stdcall;
function WD_AI_AsyncClear (CardNumber:Word; var StartPos:Cardinal; var AccessCnt:Cardinal):Smallint;stdcall;
function WD_AI_AsyncClearEx (CardNumber:Word; var StartPos:Cardinal; var AccessCnt:Cardinal;NoWait:Cardinal):Smallint;stdcall;
function WD_AI_AsyncDblBufferHalfReady (CardNumber:Word; var HalfReady:Byte; var StopFlag:Byte):Smallint;stdcall;
function WD_AI_AsyncDblBufferMode (CardNumber:Word; Enable:Byte):Smallint;stdcall;
function WD_AI_AsyncDblBufferToFile (CardNumber:Word):Smallint;stdcall;
function WD_AI_ContBufferSetup (CardNumber:Word; var Buffer:array of smallint; ReadCount:Cardinal; var BufferId:Word):Smallint;stdcall;
function WD_AI_ContBufferReset (CardNumber:Word):Smallint;stdcall;
function WD_AI_ConvertCheck (CardNumber:Word; var Stopped:Byte):Smallint;stdcall;
function WD_AI_DMA_Transfer (CardNumber:Word):Smallint;stdcall;
function WD_AI_AsyncReStartNextReady (CardNumber:Word; var DaqReady:Byte; var StopFlag:Byte; var RdyDaqCnt:Word):Smallint;stdcall;
function WD_AI_EventCallBack (CardNumber:Word; mode:Smallint; EventType:Smallint; callbackAddr:Cardinal):Smallint;stdcall;
function WD_AI_GetEvent(CardNumber:Word; var hEvent:Cardinal):Smallint;stdcall;
function WD_AI_ContBufferLock (CardNumber:Word; var Buffer:Cardinal; ReadCount:Cardinal; var BufferId:Word):Smallint;stdcall;
function WD_AI_DMA_TransferBySize (CardNumber:Word; timeLimit:Single; BufId:Word; ReadCount:Cardinal; var numRead:Cardinal; var dataNotTransferred:Cardinal; var complete:Byte):Smallint;stdcall;
function WD_AI_SetTimeout (CardNumber:Word; msec:Cardinal):Smallint;stdcall;
function WD_AI_AsyncReTrigNextReady (CardNumber:Word; var trgReady:Byte; var StopFlag:Byte; var RdyTrigCnt:Cardinal):Smallint;stdcall;
function WD_AI_AsyncDblBufferHandled (CardNumber:Word):Smallint;stdcall;
function WD_AI_AsyncDblBufferOverrun (CardNumber:Word; op:Word; var overrunFlag:Word):Smallint;stdcall;
(*---------------------------------------------------------------------------*)
function WD_SSI_SourceConn (CardNumber:Word; sigCode:Word):Smallint;stdcall;
function WD_SSI_SourceDisConn (CardNumber:Word; sigCode:Word):Smallint;stdcall;
function WD_SSI_SourceClear (CardNumber:Word):Smallint;stdcall;
function WD_Route_Signal (CardNumber:Word; signal:Word; Line:Word; dir:Word):Smallint;stdcall;
function WD_Signal_DisConn (CardNumber:Word; signal:Word; Line:Word):Smallint;stdcall;
(*---------------------------------------------------------------------------*)
function WD_AD_Auto_Calibration_ALL(CardNumber:Word):Smallint;stdcall;
function WD_EEPROM_CAL_Constant_Update(CardNumber:Word; bank:Word):Smallint;stdcall;
function WD_Load_CAL_Data(CardNumber:Word; bank:Word):Smallint;stdcall;
function WD_Set_Default_Load_Area(CardNumber:Word; bank:Word):Smallint;stdcall;
function WD_Get_Default_Load_Area(CardNumber:Word):Smallint;stdcall;
(*---------------------------------------------------------------------------*)
function WD_DI_ReadLine (CardNumber:Word; Port:Word; Line:Word; var State:Word):Smallint;stdcall;
function WD_DI_ReadPort (CardNumber:Word; Port:Word; var Value:Cardinal):Smallint;stdcall;
(*---------------------------------------------------------------------------*)
function WD_DO_WriteLine (CardNumber:Word; Port:Word; Line:Word; Value:Word):Smallint;stdcall;
function WD_DO_WritePort (CardNumber:Word; Port:Word; Value:Cardinal):Smallint;stdcall;
function WD_DO_ReadLine (CardNumber:Word; Port:Word; Line:Word; var Value:Word):Smallint;stdcall;
function WD_DO_ReadPort (CardNumber:Word; Port:Word; var Value:Cardinal):Smallint;stdcall;
(*---------------------------------------------------------------------------*)
function WD_DIO_PortConfig (CardNumber:Word; Port:Word; Mode:Word; Direction:Word):Smallint;stdcall;
function WD_DIO_LineConfig (CardNumber:Word; Port:Word; Line:Cardinal; Direction:Word):Smallint;stdcall;
function WD_DIO_LinesConfig (CardNumber:Word; Port:Word; Mode:Word; wLinesdirmap:Cardinal):Smallint;stdcall;

implementation

function WD_Register_Card; external 'WD-Dask.dll';
function WD_Register_Card_By_PXISlot_GA; external 'WD-Dask.dll';
function WD_Release_Card; external 'WD-Dask.dll';
function WD_Get_SDRAMSize; external 'WD-Dask.dll';
function WD_SoftTriggerGen; external 'WD-Dask.dll';
function WD_GetActualRate; external 'WD-Dask.dll';
function WD_GetBaseAddr; external 'WD-Dask.dll';
function WD_GetPXIGeographAddr; external 'WD-Dask.dll';
function WD_Buffer_Alloc; external 'WD-Dask.dll';
function WD_Buffer_Free; external 'WD-Dask.dll';
function WD_Device_Scan; external 'WD-Dask.dll';
(*---------------------------------------------------------------------------*)
function WD_AI_Config; external 'WD-Dask.dll';
function WD_AI_Trig_Config; external 'WD-Dask.dll';
function WD_AI_Set_Mode; external 'WD-Dask.dll';
function WD_AI_CH_Config; external 'WD-Dask.dll';
function WD_AI_CH_ChangeParam; external 'WD-Dask.dll';
function WD_AI_InitialMemoryAllocated; external 'WD-Dask.dll';
function WD_AI_VoltScale; external 'WD-Dask.dll';
function WD_AI_ContReadChannel; external 'WD-Dask.dll';
function WD_AI_ContReadMultiChannels; external 'WD-Dask.dll';
function WD_AI_ContScanChannels; external 'WD-Dask.dll';
function WD_AI_ContReadChannelToFile; external 'WD-Dask.dll';
function WD_AI_ContReadMultiChannelsToFile; external 'WD-Dask.dll';
function WD_AI_ContScanChannelsToFile; external 'WD-Dask.dll';
function WD_AI_ContVScale; external 'WD-Dask.dll';
function WD_AI_ContStatus; external 'WD-Dask.dll';
function WD_AI_AsyncCheck; external 'WD-Dask.dll';
function WD_AI_AsyncClear; external 'WD-Dask.dll';
function WD_AI_AsyncClearEx; external 'WD-Dask.dll';
function WD_AI_AsyncDblBufferHalfReady; external 'WD-Dask.dll';
function WD_AI_AsyncDblBufferMode; external 'WD-Dask.dll';
function WD_AI_AsyncDblBufferToFile; external 'WD-Dask.dll';
function WD_AI_ContBufferSetup; external 'WD-Dask.dll';
function WD_AI_ContBufferReset; external 'WD-Dask.dll';
function WD_AI_DMA_Transfer; external 'WD-Dask.dll';
function WD_AI_ConvertCheck; external 'WD-Dask.dll';
function WD_AI_AsyncReStartNextReady; external 'WD-Dask.dll';
function WD_AI_EventCallBack; external 'WD-Dask.dll';
function WD_AI_GetEvent; external 'WD-Dask.dll';
function WD_AI_ContBufferLock; external 'WD-Dask.dll';
function WD_AI_DMA_TransferBySize; external 'WD-Dask.dll';
function WD_AI_SetTimeout; external 'WD-Dask.dll';
function WD_AI_AsyncReTrigNextReady; external 'WD-DASK.dll';
function WD_AI_AsyncDblBufferHandled; external 'WD-DASK.dll';
function WD_AI_AsyncDblBufferOverrun; external 'WD-DASK.dll';
function WD_OutTrig_Config; external 'WD-Dask.dll';
(*---------------------------------------------------------------------------*)
function WD_SSI_SourceConn; external 'WD-Dask.dll';
function WD_SSI_SourceDisConn; external 'WD-Dask.dll';
function WD_SSI_SourceClear; external 'WD-Dask.dll';
function WD_Route_Signal; external 'WD-Dask.dll';
function WD_Signal_DisConn; external 'WD-Dask.dll';
(*---------------------------------------------------------------------------*)
function WD_AD_Auto_Calibration_ALL; external 'WD-Dask.dll';
function WD_EEPROM_CAL_Constant_Update; external 'WD-Dask.dll';
function WD_Load_CAL_Data; external 'WD-Dask.dll';
function WD_Set_Default_Load_Area; external 'WD-Dask.dll';
function WD_Get_Default_Load_Area; external 'WD-Dask.dll';
(*---------------------------------------------------------------------------*)
function WD_DI_ReadLine; external 'WD-DASK.dll';
function WD_DI_ReadPort; external 'WD-DASK.dll';
(*---------------------------------------------------------------------------*)
function WD_DO_WriteLine; external 'WD-DASK.dll';
function WD_DO_WritePort; external 'WD-DASK.dll';
function WD_DO_ReadLine; external 'WD-DASK.dll';
function WD_DO_ReadPort; external 'WD-DASK.dll';
(*---------------------------------------------------------------------------*)
function WD_DIO_PortConfig; external 'WD-DASK.dll';
function WD_DIO_LineConfig; external 'WD-DASK.dll';
function WD_DIO_LinesConfig; external 'WD-DASK.dll';

end.
