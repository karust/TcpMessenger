package main

import (
	"fmt"

	"github.com/jinzhu/gorm"
)

// Session ... Session
type Session struct {
	conn *Conn
	db   *gorm.DB
	uid  uint
}

// Register ... opc=?, nlen(H), name(S), plen(H), pass(S)
// Authenticate account or create new if not exists
func (sess *Session) Register(reader *PacketReader) uint {

	nameLen := reader.Short()
	name := reader.String(nameLen)
	passLen := reader.Short()
	pass := reader.String(passLen)

	acc := Account{}
	sess.db.First(&acc, "login = ?", name)

	if sess.conn.uidConn[acc.ID] != nil {
		Unauthorized(sess.conn)
		return 0
	}

	//fmt.Println("Acc:", acc)
	// If no such account - create it
	if acc.Login == "" {
		sess.db.Create(&Account{Login: name, Pass: pass})
		sess.uid = acc.ID
		OK(sess.conn, acc.ID)
		return sess.uid
	} else if pass == acc.Pass {
		sess.uid = acc.ID
		OK(sess.conn, acc.ID)
		return sess.uid
	} else {
		Unauthorized(sess.conn)
		return 0
	}
}

// Contacts ... opc 10, ALL (byte), nameLen (Short), name, ID (Long)
// if all - send all contacts, else see required name, if no name look ID
// return contacts info
func (sess *Session) Contacts(reader *PacketReader) {
	all := reader.Byte()
	if all == 1 {
		accs := []Account{}
		sess.db.Find(&accs)
		SendContacts(sess.conn, accs)
		return
	}
	// Now I return all contacts in DB, need some logic here to solve it
}

// Message ...  opc = 1, group?(B), ID(Q), tlen(H), text(S)
// Message can be either to group or individual contact
func (sess *Session) Message(reader *PacketReader) {
	isGroup := reader.Byte()
	id := uint(reader.Long())
	tlen := reader.Short()
	text := reader.String(tlen)
	if isGroup == 0 {
		recipentConn := sess.conn.uidConn[id]

		if recipentConn == nil {
			fmt.Println(id, "not online")
			return
		}
		if sess.uid != id {
			//fmt.Println("Message from uid ", uid)
			SendMessage(recipentConn, 0, sess.uid, text)
		}
	} else {
		fmt.Println(id)
		membersOfGroup := []GroupMemebers{}
		sess.db.Where("g_id = ?", id).Find(&membersOfGroup)

		ableToSend := false
		for _, c := range membersOfGroup {
			if c.UID == sess.uid {
				ableToSend = true
			}
		}
		if ableToSend {
			for i, c := range membersOfGroup {
				fmt.Println(i, ") Send to:", c.UID, sess.conn.uidConn[c.UID])

				recipentConn := sess.conn.uidConn[c.UID]
				fmt.Println(recipentConn)
				if recipentConn == nil {
					continue
				}
				if sess.uid != c.UID {
					SendMessage(recipentConn, 1, id, text)
				}
			}
		} else {
			ErrorResponse(sess.conn, "You are not member of this group")
		}
	}

}

// Sticker ...  opc=2, group?(B), ID(Q), stPack(H), stNum(H)
// Sticker can also be either for group or contact
func (sess *Session) Sticker(reader *PacketReader) {
	isGroup := reader.Byte()
	id := uint(reader.Long())
	stPack := reader.Short()
	stNum := reader.Short()
	if isGroup == 0 {
		recipentConn := sess.conn.uidConn[id]
		if recipentConn == nil {
			fmt.Println(id, "not online")
			return
		}
		if sess.uid != id {
			SendSticker(recipentConn, 0, sess.uid, stPack, stNum)
		}
	} else {
		fmt.Println(id)
		membersOfGroup := []GroupMemebers{}
		sess.db.Where("g_id = ?", id).Find(&membersOfGroup)
		for _, c := range membersOfGroup {
			recipentConn := sess.conn.uidConn[c.UID]
			if recipentConn == nil {
				continue
			}
			if sess.uid != c.UID {
				SendSticker(recipentConn, 1, sess.uid, stPack, stNum)
			}
		}
	}
}

// CreateGroup ... opc=3, tlen(H), name(S)
func (sess *Session) CreateGroup(reader *PacketReader) {
	fmt.Println("CrGr")
	tlen := reader.Short()
	name := reader.String(tlen)

	group := Group{Name: name, AdminID: sess.uid, MembersNum: 1}
	err := sess.db.Create(&group)
	// If unique constraint failed no response now
	fmt.Println("CreateGroup:", err)

	grMem := GroupMemebers{GID: group.ID, UID: sess.uid}
	err = sess.db.Create(&grMem)
	fmt.Println("CreateGroup2:", err)

	groups := []Group{}
	sess.db.Find(&groups)
	GroupInfo(sess.conn, groups)
	//fmt.Println(group)
	//GroupInfo(sess.conn, []Group{group})
}

// DelAddUserGroup ... opc=5, GID(Q), UID(Q)
func (sess *Session) DelAddUserGroup(reader *PacketReader) {

	gid := reader.Long()
	uid := reader.Long()

	group := Group{}
	sess.db.First(&group, "id = ?", gid)

	if group.AdminID == sess.uid || uid == uint64(sess.uid) {
		fmt.Println("Gid, Uid", gid, uid)
		sess.db.Delete(GroupMemebers{}, "g_id = ? AND uid = ?", gid, uid)
		//sess.db.Where("g_id = ?", gid).Find(&membersOfGroup)
		group := Group{}
		sess.db.Where("id = ?", gid).Find(&group)

		if group.MembersNum != 0 {
			group.MembersNum--
		}
		sess.db.Save(&group)
		//for _, m := range membersOfGroup {
		//	if m.UID == uint(uid) {
		//		sess.db.Delete(&m)
		//	}
		//}
		groups := []Group{}
		sess.db.Find(&groups)
		GroupInfo(sess.conn, groups)
	} else {
		ErrorResponse(sess.conn, "You are not admin of this group")

	}
}

// JoinGroup ... opc=6, GID(Q)
func (sess *Session) JoinGroup(reader *PacketReader) {
	gid := uint(reader.Long())
	fmt.Println("GID:", gid)

	grMem := GroupMemebers{GID: gid, UID: sess.uid}
	if result := sess.db.Create(&grMem); result.Error != nil {
		ErrorResponse(sess.conn, "You already member of this group")
		return
	}

	group := Group{}
	sess.db.Where("id = ?", gid).Find(&group)
	fmt.Println(group)
	group.MembersNum++
	sess.db.Save(&group)

	//groupIDuserIDs[grmem.GID] = append(groupIDuserIDs[grmem.GID], grmem.UID)
	//userIDgroupIDs[grmem.UID] = append(userIDgroupIDs[grmem.UID], grmem.GID)

	groups := []Group{}
	sess.db.Find(&groups)
	GroupInfo(sess.conn, groups)
}

// GetGroups ... opc=7, count (B), nlen(H), name(S)
func (sess *Session) GetGroups(reader *PacketReader) {
	//count := reader.Byte()
	//nlen := reader.Short()
	//name := reader.String(nlen)

	//if count == 0 {
	//uid := sess.uid
	groups := []Group{}
	/*groupsIDs := userIDgroupIDs[sess.uid]
	for _, i := range groupsIDs {
		group := Group{}
		sess.db.Where("ID = ?", i).Find(&group)
		groups = append(groups, group)
	}*/
	sess.db.Find(&groups)
	fmt.Println(groups)
	GroupInfo(sess.conn, groups)
	//}
}
