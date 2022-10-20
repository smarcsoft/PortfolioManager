import {Component} from 'react';
import { Stack, TextField } from '@fluentui/react';
import './App.css';

//export class Console extends React.Component <{lines:string[], currentline:number}>{
export class Console extends Component <{text:string}>{

    //constructor(props: { lines: string[], currentline:0 } | Readonly<{ lines: string[], currentline:0 }>)
    // constructor(props: { text: string} | Readonly<{ text: string}>)
    // {
    //   super(props)
    //   //let lines = ["Checking infrastructure...", "", "", "", ""]
    // }
    render() {
      return (
          <Stack className='code'>
            {/* <Stack.Item align="center" style={{width:'500px',height:'100px'}} className='code'> */}
              <TextField borderless={true} className='code' resizable={false} inputClassName='code' readOnly={true} multiline={true} autoAdjustHeight={true} value={this.props.text}></TextField>  
              {/* <Text id='l1' className={this.props.currentline==0?'code cursor':'code'} variant={'large'}>{this.props.lines[0]}</Text><br/>
              <Text id='l2' className={this.props.currentline==1?'code cursor':'code'} variant={'large'}>{this.props.lines[1]}</Text><br/>
              <Text id='l3' className={this.props.currentline==2?'code cursor':'code'} variant={'large'}>{this.props.lines[2]}</Text><br/>
              <Text id='l4' className={this.props.currentline==3?'code cursor':'code'} variant={'large'}>{this.props.lines[3]}</Text><br/>
              <Text id='l5' className={this.props.currentline==4?'code cursor':'code'} variant={'large'}>{this.props.lines[4]}</Text><br/> */}
            {/* </Stack.Item> */}
          </Stack>
      );
    }
}