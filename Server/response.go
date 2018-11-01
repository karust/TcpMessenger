package main

import (
	"fmt"
)

// Unauthorized ... Resonse on Register packet
func Unauthorized(conn *Conn) {
	w := CreatePacketWriter(401)
	w.Send(conn)
}

// OK ... OK response
func OK(conn *Conn, uid uint) {
	w := CreatePacketWriter(200)
	w.Long(uint64(uid))
	w.Send(conn)
}

// SendContacts ... Sends Contacts, Opcode=255
func SendContacts(conn *Conn, accounts []Account) {
	w := CreatePacketWriter(255)

	contLen := byte(len(accounts))
	w.Byte(contLen)
	for _, acc := range accounts {
		w.Long(uint64(acc.ID))
		logLen := uint16(len(acc.Login))
		w.Short(logLen)
		w.String(acc.Login)
	}
	w.Send(conn)
}

// SendMessage ... opc=254, group?(B), uid(Q), tlen(H), text(S)
// uid - id of user who sends
func SendMessage(conn *Conn, group byte, uid uint, text string) {
	fmt.Println(text, "from -", uid)
	w := CreatePacketWriter(254)
	w.Byte(group)
	w.Long(uint64(uid))
	tLen := uint16(len(text))
	w.Short(tLen)
	w.String(text)
	w.Send(conn)
}

// SendSticker ... opc=253, uid(Q), stPack(H), stNum(H)
// uid - id of user who sends
func SendSticker(conn *Conn, group byte, uid uint, stPack uint16, stNum uint16) {
	w := CreatePacketWriter(253)
	w.Byte(group)
	w.Long(uint64(uid))
	w.Short(stPack)
	w.Short(stNum)
	w.Send(conn)
}

// GroupInfo ...
// opc=252, Count (byte), nameLen (Short), name(text), ID (Long), Members (Int)
func GroupInfo(conn *Conn, groups []Group) {
	w := CreatePacketWriter(252)

	count := byte(len(groups))
	w.Byte(count)
	for _, gr := range groups {
		nameLen := uint16(len(gr.Name))
		w.Short(nameLen)
		w.String(gr.Name)
		w.Long(uint64(gr.ID))
		w.Int(gr.MembersNum)
	}
	w.Send(conn)
}

// ErrorResponse ... opc=251, errLen(H), errText(S)
func ErrorResponse(conn *Conn, message string) {
	w := CreatePacketWriter(251)

	msgLen := uint16(len(message))
	w.Short(msgLen)
	w.String(message)
	w.Send(conn)
}
