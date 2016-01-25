import sys
import xbmcgui
import copy

CANCEL_DIALOG  = ( 9, 10, 92, 216, 247, 257, 275, 61467, 61448, )
ACTION_CONTEXT_MENU = ( 117, )

class GUI( xbmcgui.WindowXMLDialog ):
    def __init__( self, *args, **kwargs ):
        xbmcgui.WindowXMLDialog.__init__( self )
        self.labels = kwargs[ "labels" ]
        self.buttons = []

    def onInit( self ):
        self._show_context_menu()

    def _show_context_menu( self ):
        self._hide_buttons()
        self._setup_menu()
        self.setFocus( self.buttons[0])

    def _hide_buttons( self ):
        for i in range( 3 ):
            self.getControl( i + 1001 ).setVisible( False )
            self.getControl( i + 1001 ).setEnabled( False )

        for i in range( len( self.buttons ) ):
            self.getControl( self.buttons[i] ).setVisible( False )
    
    def _setup_menu( self ):
        dialog_posx, dialog_posy = self.getControl( 999 ).getPosition()
        dialog_height = self.getControl( 999 ).getHeight()
        model_button = self.getControl( 1001 )
        button_posx, button_posy = model_button.getPosition()
        button_height = model_button.getHeight()
        extra_height =  (len( self.labels ) - 1) * button_height
        dialog_height = dialog_height + extra_height
        dialog_posy = dialog_posy - (extra_height / 2)
        button_posy = button_posy - (extra_height / 2)
        self.getControl( 999 ).setPosition( dialog_posx, dialog_posy )
        self.getControl( 999 ).setHeight( dialog_height )
        for i in range( len( self.labels ) ):
            button = self._createButton(self.labels[ i ], button_posx, button_posy + ( button_height * i ))
        self.addControls(self.buttons)
        for i in range( len( self.buttons ) ):
            button = self.buttons[i]
            next = i+1 if i+1 <= len( self.buttons ) -1 else 0
            prev = i-1 if i-1 >= 0 else len( self.buttons ) -1
            button.controlLeft(self.buttons[prev])
            button.controlRight(self.buttons[next])
            button.controlUp(self.buttons[prev])
            button.controlDown(self.buttons[next])
            button.setVisible( True )
            button.setEnabled( True )
        
    def _createButton(self, label, button_posx, button_posy):
        button_index = len(self.buttons)
        button = xbmcgui.ControlButton(
            x=button_posx, y=button_posy, width=320, height=38, label=label, 
            focusTexture="button-focus.png", 
            noFocusTexture="button-nofocus.png", 
            textOffsetX=0, 
            textOffsetY=0, 
            alignment=6,)
        button.setLabel(
            label=label, 
            font="font-20", 
            textColor='0x88FFFFFF',
            focusedColor='0xFFFFFFFF')
        self.buttons.append(button)
        return button

    def _close_dialog( self, selection=None ):
        self.selection = selection
        self.close()
        
    def onClick( self, controlId ):
        self._close_dialog( controlId - 3001 )

    def onFocus( self, controlId ):
        pass

    def onAction( self, action ):
        if ( action.getId() in CANCEL_DIALOG ) or ( action.getId() in ACTION_CONTEXT_MENU ):
            self._close_dialog()
