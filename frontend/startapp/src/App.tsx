import {Component} from 'react';
import { ThemeProvider, PartialTheme, Stack, CompoundButton, IStackTokens } from '@fluentui/react';
import './App.css';
import { Console } from './Console';


interface ServerStatus{
  status_code: number,
  message: string,
  ip:string
}

interface SystemStatus{
  status: number,
  details: string
}

const SHUTTING_DOWN:number = 32;
const TERMINATED:number = 48;
const STOPPING:number = 64;
const STOPPED:number = 80;
const PENDING:number = 0;
const RUNNING:number = 16;
const NOT_KNOWN:number  = -1;

const SERVICES_URL='http://44.211.192.23:5000/services'
const JUPYTER_SERVICES_URL='http://44.211.192.23:5000/jupyter'

const appTheme: PartialTheme = {
  palette: {
    themePrimary: '#96d2ff',
    themeLighterAlt: '#06080a',
    themeLighter: '#182229',
    themeLight: '#2d3f4d',
    themeTertiary: '#79bbed',
    themeSecondary: '#85ccff',
    themeDarkAlt: '#a1d6ff',
    themeDark: '#b0ddff',
    themeDarker: '#c4e6ff',
    neutralLighterAlt: '#4f4f4f',
    neutralLighter: '#565656',
    neutralLight: '#626262',
    neutralQuaternaryAlt: '#696969',
    neutralQuaternary: '#6f6f6f',
    neutralTertiaryAlt: '#878787',
    neutralTertiary: '#f3f3f3',
    neutralSecondary: '#f5f5f5',
    neutralSecondaryAlt: '#f5f5f5',
    neutralPrimaryAlt: '#f7f7f7',
    neutralPrimary: '#ededed',
    neutralDark: '#fbfbfb',
    black: '#fdfdfd',
    white: '#474747',
  }};

const stackTokens: IStackTokens = { childrenGap: 40 };

//export class App extends React.Component<{}, {lines:string[]}> {
export class App extends Component<{}, {console_text:string}> {
  currentline: number;
  cursorline: number;
  // Initial button states
  start_disabled:boolean = true;
  start_checked:boolean = false;
  stop_disabled:boolean = true;
  stop_checked:boolean = false;
  launch_disabled:boolean = true;
  launch_checked:boolean = false;
  compute_ip:string = "";

  constructor(props: {})
  {
    super(props)
//    this.state={lines:["Checking compute server...", "", "", "", ""]};
    this.state={console_text:"Checking compute server..."}
    this.currentline = 1;
    this.cursorline = 0;
    this.stopPM = this.stopPM.bind(this);
    this.startPM = this.startPM.bind(this);
    this.launchPM = this.launchPM.bind(this);
  }
  render() {
    return (
      <ThemeProvider theme={appTheme}>
        <Stack>
          <Stack.Item align="center" style={{fontSize:"27px", height:'100px'}}>
            Smarcsoft Porfolio Management
          </Stack.Item>
          <Stack.Item align="center">
            {/* <Console lines={this.state.lines} currentline={this.cursorline}/> */}
            <Console text={this.state.console_text}/>
            <Stack horizontal tokens={stackTokens}>
              <CompoundButton secondaryText="This is starting the underlying compute server." onClick={this.startPM} disabled={this.start_disabled} checked={this.start_checked}>
                Start Portfolio Manager
              </CompoundButton>
              <CompoundButton secondaryText="This is stopping the underlying compute server." onClick={this.stopPM} disabled={this.stop_disabled} checked={this.stop_checked}>
                Stop Portfolio Manager
              </CompoundButton>
              <CompoundButton primary secondaryText="Click here to launch Portfolio Manager." onClick={this.launchPM} disabled={this.launch_disabled} checked={this.launch_checked}>
                Launch!
              </CompoundButton>
            </Stack>
          </Stack.Item>
        </Stack>
      </ThemeProvider>
    );
  }

  async stopPM():Promise<void> {
    console.log("stopPM called on " + this)
    this.clearconsole();
    this.addline("Stopping compute server")
    let st = await this.stop_compute();
    this.button_states_on_status(st);
    this.addlineWithStatus(st);
    if((st.status_code === SHUTTING_DOWN ) || (st.status_code === STOPPING))
    {
      st = await this.wait_for_stop();
      this.addlineWithStatus(st)
      this.button_states_on_status(st);
    }
  }


  async addlineWithStatus(status:ServerStatus)
  {
    console.log("print status "+status.status_code+"...")
    switch(status.status_code)
    {
      case NOT_KNOWN:
      case TERMINATED:
      case STOPPED:
        this.addline("Stopped")
        break;
      case SHUTTING_DOWN:
        this.addline("Shutting down");
        break;
      case STOPPING:
        this.addline("Stopping... This can take a few minutes")
        break;
      case PENDING:
        this.addline("Pending...")
        break;
      case RUNNING:
        this.addline("Running")
        break;
    }
  }

  async button_states_on_status(st:ServerStatus)
  {
    console.log("Updating button states...("+st.status_code+")")
    switch(st.status_code)
    {
      case NOT_KNOWN:
      case TERMINATED:
      case STOPPED:
        console.log("NOT_KNOWN|TERMINATED|STOPPED");
        // Start button is enabled and unchecked.
        this.button_states(true,false,false,true, false, false);
        this.setState(this.state);
        break;
      case SHUTTING_DOWN:
        console.log("SHUTTING_DOWN");
        this.button_states(false,false,false,false,false, false);
        this.setState(this.state);
        break;
      case STOPPING:
        console.log("STOPPING");
        this.button_states(false,false,false,false, false, false);
        this.setState(this.state);
        break;
      case PENDING:
        console.log("PENDING");
        this.button_states(false,true,false,false, false, false);
        this.setState(this.state);
        break;
      case RUNNING:
        console.log("RUNNING");
        this.button_states(false,true,true,false, true, false);
        this.setState(this.state);
        break;
    }
  }

  async startPM():Promise<void> {
    try{
      this.clearconsole();
      this.addline("Starting compute server...");
      await this.start_infrastructure();
      this.addline("Launching financial data science platform...")
      // Wait 15 seconds, the time usually needed by AWS to accept incoming connections.
      await new Promise( resolve => setTimeout(resolve, 15000) );
      await this.start_jupyter_server();
      this.addline("Launched!")
    }
    catch(e)
    {
      this.addline(""+e);
    }
  }

  launchPM():void {
    if(this.compute_ip !== ""){
      console.log("Redirecting to http://"+this.compute_ip+":9999/tree");
      window.location.href="http://"+this.compute_ip+":9999/tree";
    }
  }

  componentDidMount(): void {
    this.start()
  }

  private button_states(start_enabled:boolean, start_checked:boolean, stop_enabled:boolean, stop_checked:boolean, launch_enabled:boolean, launch_checked:boolean)
  {
    this.start_disabled=!start_enabled;
    this.start_checked=start_checked;
    this.stop_disabled=!stop_enabled;
    this.stop_checked = stop_checked;
    this.launch_disabled = !launch_enabled;
    this.launch_checked = launch_checked;
  }

  async start()
  {
    try{
      let st:ServerStatus = await this.get_server_status();
      this.button_states_on_status(st);
      this.addlineWithStatus(st);
      if(st.status_code === RUNNING)
      {
        this.compute_ip = st.ip;
        console.log("Compute server IP: " + this.compute_ip);
      } 
    }
  catch(e)
  {
    this.addline(""+e);
  }
    
  }



  async start_infrastructure():Promise<ServerStatus>
  {
    this.button_states_on_status({status_code:RUNNING, message:"", ip:""}); //to disable the start button as soon as pressed
    let ss:ServerStatus = await this.start_compute();
    this.button_states_on_status(ss);
    // Check if started
    // Wait for the infrastructure to startup for 5 times 5 seconds
    if((ss.status_code === NOT_KNOWN) || (ss.status_code === PENDING))
    {
      this.addlineWithStatus(ss);
      console.log("Waiting for start completion...("+ss.status_code+")");
      ss=await this.wait_for_start();
      this.addlineWithStatus(ss);
      this.button_states_on_status(ss);
      return ss;
    }
    throw new Error("Infrastructure could not be started. Code " + ss.status_code+". Details:"+ss.message);
  }

  async start_jupyter_server():Promise<SystemStatus>
  {
    console.log("sending POST "+JUPYTER_SERVICES_URL);
    const response =  await fetch(JUPYTER_SERVICES_URL,{method:'POST'});
    if(response.ok){
      console.log("response ok");
      let myjson = await response.json()
      return myjson as Promise<SystemStatus>
    }
    else{
      throw new Error("Could not start data science platform...");
    }
  }

  async wait_for_start():Promise<ServerStatus>
  {
    let ss:ServerStatus={status_code:NOT_KNOWN, message:"", ip:""};

    for(let i=1;i<=5;i++)
    {
      ss = await this.get_server_status();
      if((ss.status_code === NOT_KNOWN) || (ss.status_code === PENDING))
      {
        console.log("Waiting for start completion...("+ss.status_code+")");
        await new Promise( resolve => setTimeout(resolve, 5000) );
      }
      else
      {
        console.log("Quitting wait for start completion loop with status "+ss.status_code);
        break;
      }
    }
    switch(ss.status_code)
    {
      case NOT_KNOWN:
      case SHUTTING_DOWN:// shutting down
      case TERMINATED:// terminated
      case STOPPING:// stopping
      case STOPPED:// stopped
        // Infrastructure could not be started for some reason
        console.log("wait_for_start is still stopped|not known| shutting down|terminated| stopping ("+ss.status_code+"). Exception raised ("+ss.status_code+")");
        throw new Error("Infrastructure could not be started ("+ ss.status_code+")");
      case PENDING: //Infrastructure is still pending
      console.log("wait_for_start is still pending. Exception raised ("+ss.status_code+")");
        throw new Error("Infrastructure is still in pending state. Giving up...");
      case RUNNING://running
        // Store the compute server IP address
        console.log("Updating compute server IP address: " + ss.ip);
        this.compute_ip = ss.ip;
        console.log("wait_for_start returns RUNNING ("+ss.status_code+")");
        return ss;
    }
    throw new Error("Could not start infrastructure. Status code:"+ ss.status_code);
  }


  async wait_for_stop():Promise<ServerStatus>
  {
    console.log("wait for stop completion")
    let ss:ServerStatus={status_code:NOT_KNOWN, message:"", ip:""};

    for(let i=1;i<=60;i++) // waits for up to 5 minutes
    {
      let ss = await this.get_server_status();
      if((ss.status_code === STOPPING) || (ss.status_code === SHUTTING_DOWN) || (ss.status_code=== NOT_KNOWN))
      {
        console.log("STOPPING|SHUTTING_DOWN ("+ss.status_code+")")
        await new Promise( resolve => setTimeout(resolve, 5000) );
      }
      else
      {
        console.log("quitting wait loop with statsus "+ss.status_code)
        break;
      }
    }
    switch(ss.status_code)
    {
      case RUNNING:
      case SHUTTING_DOWN:// shutting down
      case STOPPING:// stopping
        throw new Error("Infrastructure could not be stopped ("+ ss.status_code+")");
      case PENDING: //Infrastructure is still pending
        throw new Error("Infrastructure is still in pending state. Giving up...");
      case STOPPED:
      case NOT_KNOWN:
        this.compute_ip="";
        return ss;
    }
    throw new Error("Could not stop infrastructure. Status code:"+ ss.status_code);
  }


  private async start_compute()
  {
    console.log("sending POST "+SERVICES_URL);
    const response =  await fetch(SERVICES_URL,{method:'POST'});
    if(response.ok){
      console.log("response ok");
      let myjson = await response.json()
      return myjson as Promise<ServerStatus>
    }
    else{
      throw new Error("Could not start compute server...");
    }
  }

  private async stop_compute()
  {
    const response =  await fetch(SERVICES_URL,{method:'DELETE'});
    if(response.ok){
      let myjson = await response.json()
      return myjson as Promise<ServerStatus>
    }
    else{
      throw new Error("Could not stop compute server...");
    }
  }


  clearconsole()
  {
    //this.state={lines:["", "", "", "", ""]};
    //this.state={console_text:""};
    this.currentline = 0;
    this.setState({console_text:""});
  }

  addline(line:string)
  {
    // this.state={console_text:this.state.console_text+"\n"+line};
 //   this.state.lines[this.currentline]=line;
  //  this.cursorline = this.currentline;
    this.setState({console_text:this.state.console_text+"\n"+line}); // Triggers the component rendering and its children
    this.currentline++;
  }

  async get_server_status():Promise<ServerStatus>
  {
    try {
      const response =  await fetch(SERVICES_URL,{method:'GET'});
      if(response.ok){
        let myjson = await response.json()
        return myjson as Promise<ServerStatus>
      }
      else{
        throw new Error("Could not get compute server status:"+response.statusText);
      }
    }
    catch (e)
    {
      throw new Error("Could not get compute server status:"+e);
    }
  }
 
}



